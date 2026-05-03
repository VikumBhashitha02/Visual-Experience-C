/**
 * animation/core/easing.ts
 * Shared timing and interpolation helpers for the canvas renderer.
 */

export const clamp = (value: number, min: number, max: number): number => {
  if (value <= min) return min;
  if (value >= max) return max;
  return value;
};

export const clamp01 = (value: number): number => clamp(value, 0, 1);

export const lerp = (from: number, to: number, t: number): number =>
  from + (to - from) * t;

export const easeInQuad = (t: number): number => {
  const x = clamp01(t);
  return x * x;
};

export const easeOutQuad = (t: number): number => {
  const x = clamp01(t);
  return 1 - (1 - x) * (1 - x);
};

export const easeInOutQuad = (t: number): number => {
  const x = clamp01(t);
  if (x < 0.5) return 2 * x * x;
  return 1 - Math.pow(-2 * x + 2, 2) / 2;
};

export const easeInCubic = (t: number): number => {
  const x = clamp01(t);
  return x * x * x;
};

export const easeOutCubic = (t: number): number => {
  const x = clamp01(t);
  return 1 - Math.pow(1 - x, 3);
};

// Backward-compatible alias used by older domain modules.
export const easeOut = easeOutCubic;

export const easeInOutCubic = (t: number): number => {
  const x = clamp01(t);
  if (x < 0.5) return 4 * x * x * x;
  return 1 - Math.pow(-2 * x + 2, 3) / 2;
};

export const easeOutSine = (t: number): number => {
  const x = clamp01(t);
  return Math.sin((x * Math.PI) / 2);
};

export const easeInOutSine = (t: number): number => {
  const x = clamp01(t);
  return -(Math.cos(Math.PI * x) - 1) / 2;
};

export const easeOutBack = (t: number): number => {
  const x = clamp01(t);
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

export const smoothstep = (t: number): number => {
  const x = clamp01(t);
  return x * x * (3 - 2 * x);
};

export const smootherstep = (t: number): number => {
  const x = clamp01(t);
  return x * x * x * (x * (x * 6 - 15) + 10);
};

export const pingPong01 = (time: number): number => {
  const m = ((time % 2) + 2) % 2;
  return m <= 1 ? m : 2 - m;
};

export const pulse = (
  timeSeconds: number,
  speed = 1,
  amount = 0.08,
  base = 1,
): number => base + Math.sin(timeSeconds * speed) * amount;

export const oscillate = (
  timeSeconds: number,
  speed = 1,
  min = -1,
  max = 1,
): number => lerp(min, max, (Math.sin(timeSeconds * speed) + 1) * 0.5);

export const progress = (
  elapsedMs: number,
  startMs: number,
  durationMs: number,
): number => {
  const safeDuration = Math.max(1, durationMs);
  return clamp01((elapsedMs - startMs) / safeDuration);
};

export const fadeIn = (
  elapsedMs: number,
  delayMs = 0,
  durationMs = 500,
): number => easeOutQuad(progress(elapsedMs, delayMs, durationMs));

export const fadeOut = (
  elapsedMs: number,
  delayMs = 0,
  durationMs = 500,
): number => 1 - easeOutQuad(progress(elapsedMs, delayMs, durationMs));

function hexToRgb(color: string): { r: number; g: number; b: number } | null {
  const hex = color.trim().replace("#", "");
  if (hex.length === 3) {
    return {
      r: parseInt(`${hex[0]}${hex[0]}`, 16),
      g: parseInt(`${hex[1]}${hex[1]}`, 16),
      b: parseInt(`${hex[2]}${hex[2]}`, 16),
    };
  }
  if (hex.length === 6) {
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16),
    };
  }
  return null;
}

export function rgba(color: string, alpha: number): string {
  const a = clamp01(alpha);
  if (typeof color !== "string") return `rgba(255,255,255,${a})`;
  if (color.startsWith("rgb(")) {
    return color.replace(/^rgb\((.+)\)$/, `rgba($1,${a})`);
  }
  if (color.startsWith("rgba(")) {
    return color.replace(
      /^rgba\((\s*\d+\s*,\s*\d+\s*,\s*\d+)\s*,[^)]+\)$/,
      `rgba($1,${a})`,
    );
  }
  const rgb = hexToRgb(color);
  if (!rgb) return `rgba(255,255,255,${a})`;
  return `rgba(${rgb.r},${rgb.g},${rgb.b},${a})`;
}

export type TimelineStep = {
  at: number;
  alpha?: number;
  holdMs?: number;
  easing?: "linear" | "easeOut" | "easeInOut" | "smooth";
};

function resolveTimelineEase(
  value: number,
  easing: TimelineStep["easing"],
): number {
  const t = clamp01(value);
  if (easing === "easeOut") return easeOutCubic(t);
  if (easing === "easeInOut") return easeInOutSine(t);
  if (easing === "smooth") return smootherstep(t);
  return t;
}

export function computeTimelineAlpha(
  actor: { timeline?: TimelineStep[] },
  elapsedMs: number,
  baseAlpha: number,
): number {
  const timeline = Array.isArray(actor?.timeline)
    ? actor.timeline
        .filter((step) => step && Number.isFinite(step.at))
        .map((step) => ({
          ...step,
          at: Math.max(0, Number(step.at)),
          alpha:
            typeof step.alpha === "number"
              ? clamp01(step.alpha)
              : undefined,
          holdMs:
            typeof step.holdMs === "number" && step.holdMs > 0
              ? step.holdMs
              : undefined,
        }))
        .sort((a, b) => a.at - b.at)
    : [];

  if (timeline.length === 0) return clamp01(baseAlpha);

  const beforeFirst = timeline[0];
  if (elapsedMs < beforeFirst.at) {
    if (typeof beforeFirst.alpha === "number") {
      const intro = progress(elapsedMs, Math.max(0, beforeFirst.at - 260), 260);
      return clamp01(baseAlpha) * lerp(0, beforeFirst.alpha, smoothstep(intro));
    }
    return clamp01(baseAlpha) * fadeIn(elapsedMs, 0, 380);
  }

  let current: TimelineStep = timeline[0];
  let next: TimelineStep | null = null;

  for (let i = 0; i < timeline.length; i += 1) {
    const step = timeline[i];
    if (elapsedMs >= step.at) {
      current = step;
      next = timeline[i + 1] ?? null;
      continue;
    }
    next = step;
    break;
  }

  const currentAlpha =
    typeof current.alpha === "number" ? current.alpha : 1;
  if (!next) return clamp01(baseAlpha) * currentAlpha;

  const holdUntil = current.at + (current.holdMs ?? 0);
  if (elapsedMs < holdUntil) return clamp01(baseAlpha) * currentAlpha;

  const nextAlpha = typeof next.alpha === "number" ? next.alpha : currentAlpha;
  const t = progress(elapsedMs, holdUntil, Math.max(1, next.at - holdUntil));
  const eased = resolveTimelineEase(t, next.easing || current.easing);
  return clamp01(baseAlpha) * lerp(currentAlpha, nextAlpha, eased);
}
