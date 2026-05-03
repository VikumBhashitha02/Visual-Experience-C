/**
 * animation/actorRenderers.ts
 * Domain-agnostic actor drawing with stable layout, hierarchy, and motion polish.
 */

import {
  C,
  drawArrow,
  drawBattery,
  drawBolt,
  drawCO2,
  drawCloud,
  drawConceptPill,
  drawEducationCard,
  drawGlucose,
  drawO2,
  drawPlanet,
  drawRock,
  drawSol,
  drawSunny,
  drawSwitch,
  drawThermometer,
  drawVolcano,
  drawWaterDrop,
  drawWaveArc,
  drawWireLoop,
} from "./core/shapes";
import {
  clamp,
  clamp01,
  computeTimelineAlpha,
  fadeIn,
  lerp,
  oscillate,
  pulse,
  rgba,
} from "./core/easing";

export type RenderLaidOutActorsOptions = {
  focusActorId?: string | null;
  visualElapsedMs?: number;
  loopSegmentMs?: number;
  segmentTailPauseMs?: number;
  /** 0-based; stronger glow / slower motion on later repeats */
  loopIndex?: number;
};

type Ctx = any;

export type DrawFn = (
  ctx: Ctx,
  actor: any,
  alpha: number,
  t: number,
  W: number,
  H: number,
) => void;

type PositionedActor = any & {
  type: string;
  x: number;
  y: number;
  _radius: number;
  _importance: number;
  _z: number;
  _explicitPos: boolean;
};

const TYPE_ALIAS: Record<string, string> = {
  water_drop: "waterdrop",
  droplet: "waterdrop",
  h2o: "waterdrop",
  carbondioxide: "co2",
  carbon_dioxide: "co2",
  molecule_co2: "co2",
  oxygen: "oxygen",
  o2: "oxygen",
  molecule_o2: "oxygen",
  glucose_molecule: "glucose",
  sugar: "glucose",
  energy: "bolt",
  lightning: "bolt",
  // astronomy
  star: "star",
  moon: "moon",
  earth: "planet",
  globe: "planet",
  asteroid: "asteroid",
  comet: "comet",
  // biology
  tree: "plant",
  flower: "plant",
  stem: "plant",
  leaves: "leaf",
  roots: "root",
  herbivore: "animal",
  carnivore: "animal",
  producer: "plant",
  consumer: "animal",
  cell: "cell",
  bacteria: "bacteria",
  bacterium: "bacteria",
  // chemistry / physics
  atom: "atom",
  electron: "electron",
  proton: "proton",
  neutron: "neutron",
  // earth science
  ocean: "ocean",
  mountain: "mountain",
  // circuits
  circuit: "wire",
  wire_path: "wire",
  conductor: "wire",
  battery_cell: "battery",
  lamp: "bulb",
  light_bulb: "bulb",
  audio_wave: "wave",
  vibration: "wave",
  molecule: "molecule",
};

const DEFAULT_POSITIONS: Record<string, { x: number; y: number }> = {
  sun: { x: 0.8, y: 0.14 },
  star: { x: 0.8, y: 0.14 },
  moon: { x: 0.68, y: 0.2 },
  planet: { x: 0.54, y: 0.62 },
  asteroid: { x: 0.72, y: 0.38 },
  comet: { x: 0.76, y: 0.26 },
  plant: { x: 0.24, y: 0.79 },
  leaf: { x: 0.35, y: 0.52 },
  root: { x: 0.24, y: 0.87 },
  cloud: { x: 0.54, y: 0.17 },
  waterdrop: { x: 0.18, y: 0.82 },
  water: { x: 0.18, y: 0.82 },
  ocean: { x: 0.5, y: 0.86 },
  mountain: { x: 0.72, y: 0.56 },
  co2: { x: 0.74, y: 0.32 },
  oxygen: { x: 0.64, y: 0.2 },
  glucose: { x: 0.54, y: 0.46 },
  bolt: { x: 0.48, y: 0.4 },
  arrow: { x: 0.5, y: 0.52 },
  line: { x: 0.5, y: 0.54 },
  rock: { x: 0.75, y: 0.74 },
  volcano: { x: 0.5, y: 0.76 },
  molecule: { x: 0.52, y: 0.48 },
  atom: { x: 0.5, y: 0.46 },
  electron: { x: 0.38, y: 0.46 },
  proton: { x: 0.5, y: 0.5 },
  neutron: { x: 0.58, y: 0.5 },
  cell: { x: 0.5, y: 0.5 },
  bacteria: { x: 0.5, y: 0.5 },
  label: { x: 0.5, y: 0.16 },
  thermometer: { x: 0.84, y: 0.66 },
  bulb: { x: 0.78, y: 0.46 },
  ear: { x: 0.82, y: 0.52 },
  animal: { x: 0.56, y: 0.72 },
  battery: { x: 0.22, y: 0.5 },
  switch: { x: 0.58, y: 0.5 },
  wire: { x: 0.5, y: 0.52 },
  wave: { x: 0.3, y: 0.5 },
};

const BASE_SIZE: Record<string, number> = {
  sun: 58,
  star: 36,
  moon: 38,
  planet: 92,
  asteroid: 28,
  comet: 24,
  plant: 104,
  leaf: 54,
  root: 62,
  cloud: 58,
  waterdrop: 34,
  water: 34,
  ocean: 80,
  mountain: 70,
  co2: 36,
  oxygen: 34,
  glucose: 42,
  bolt: 40,
  rock: 52,
  volcano: 74,
  molecule: 34,
  atom: 48,
  electron: 18,
  proton: 22,
  neutron: 22,
  cell: 46,
  bacteria: 30,
  label: 22,
  thermometer: 1,
  bulb: 40,
  ear: 36,
  animal: 56,
  battery: 50,
  switch: 44,
  wire: 42,
  arrow: 40,
  line: 38,
  wave: 40,
};

const IMPORTANCE: Record<string, number> = {
  plant: 1.35,
  sun: 1.28,
  planet: 1.35,
  battery: 1.25,
  bulb: 1.22,
  cloud: 1.12,
  root: 1.12,
  glucose: 1.12,
  rock: 1.1,
  arrow: 1.08,
  wire: 1.08,
  switch: 1.08,
  label: 0.92,
  waterdrop: 0.92,
  water: 0.92,
  co2: 0.92,
  oxygen: 0.92,
};

const Z_LAYER: Record<string, number> = {
  cloud: 8,
  sun: 10,
  planet: 12,
  wire: 22,
  line: 22,
  root: 26,
  plant: 32,
  leaf: 34,
  battery: 34,
  switch: 36,
  bulb: 38,
  rock: 38,
  waterdrop: 42,
  water: 42,
  co2: 44,
  oxygen: 44,
  molecule: 44,
  glucose: 46,
  bolt: 48,
  arrow: 50,
  wave: 52,
  animal: 56,
  ear: 58,
  thermometer: 58,
  label: 60,
};

function resolveType(rawType: any, text = ""): string {
  const normalized = String(rawType || "label").toLowerCase().trim();
  const alias = TYPE_ALIAS[normalized];
  if (alias) return alias;

  if (!rawType || normalized === "label") {
    const compact = String(text || "").toLowerCase().replace(/\s+/g, "");
    if (/^(h2o|water)$/.test(compact)) return "waterdrop";
    if (/^(co2|carbondioxide)$/.test(compact)) return "co2";
    if (/^(o2|oxygen)$/.test(compact)) return "oxygen";
    if (/^(glucose|sugar|c6h)/.test(compact)) return "glucose";
    if (/battery|switch|wire|current|circuit/.test(compact)) return "battery";
    if (/leaf/.test(compact)) return "leaf";
  }

  return normalized;
}

function toNumber(value: any): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function resolveAxis(
  value: any,
  max: number,
  fallbackPx: number,
): number {
  const n = toNumber(value);
  if (n == null) return fallbackPx;
  if (Math.abs(n) <= 1.2) return n * max;
  return n;
}

function defaultPoint(type: string, W: number, H: number) {
  const slot = DEFAULT_POSITIONS[type] || DEFAULT_POSITIONS.label;
  return { x: slot.x * W, y: slot.y * H };
}

function drawFallbackAnimal(ctx: Ctx, actor: any, alpha: number, label: string) {
  const x = actor.x;
  const y = actor.y;
  const r = Math.max(16, (actor.size ?? 46) * 0.44);

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = actor.color || "#D9A56F";
  ctx.beginPath();
  ctx.ellipse(x, y, r * 1.15, r * 0.82, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#5A3D25";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "#2A1A0F";
  ctx.beginPath();
  ctx.arc(x - r * 0.24, y - r * 0.12, 2.4, 0, Math.PI * 2);
  ctx.arc(x + r * 0.24, y - r * 0.12, 2.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = "600 10px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText(label, x, y + r + 6);
  ctx.restore();
}

function drawSimpleEar(ctx: Ctx, actor: any, alpha: number) {
  const x = actor.x;
  const y = actor.y;
  const s = Math.max(14, (actor.size ?? 34) * 0.44);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#F9A825";
  ctx.strokeStyle = "#C2410C";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(x, y, s * 0.7, s, 0.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(x + s * 0.08, y + s * 0.08, s * 0.28, 0.2, 4.8);
  ctx.stroke();
  ctx.restore();
}

function drawLeafGlyph(ctx: Ctx, actor: any, alpha: number) {
  const x = actor.x;
  const y = actor.y;
  const s = Math.max(18, (actor.size ?? 46) * 0.5);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#4CAF50";
  ctx.strokeStyle = "#2E7D32";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x - s, y);
  ctx.bezierCurveTo(x - s * 0.45, y - s * 0.65, x + s * 0.45, y - s * 0.65, x + s, y);
  ctx.bezierCurveTo(x + s * 0.45, y + s * 0.65, x - s * 0.45, y + s * 0.65, x - s, y);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = rgba("#1B5E20", 0.66);
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x - s * 0.82, y);
  ctx.lineTo(x + s * 0.82, y);
  ctx.stroke();
  ctx.restore();
}

function drawRootGlyph(ctx: Ctx, actor: any, alpha: number) {
  const cx = actor.x;
  const cy = actor.y;
  const size = Math.max(20, actor.size ?? 62);
  const spread = size * 0.78;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = actor.color || "#5D4037";
  ctx.lineWidth = 3.2;
  ctx.lineCap = "round";
  [[-0.7, 0.66], [-0.35, 0.84], [0, 0.92], [0.36, 0.82], [0.72, 0.66]].forEach(([dx, dy]) => {
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + spread * dx, cy + spread * dy);
    ctx.stroke();
  });
  ctx.restore();
}

function drawBulb(ctx: Ctx, actor: any, alpha: number, t: number) {
  const x = actor.x;
  const y = actor.y;
  const r = Math.max(10, (actor.size ?? 36) * 0.5);
  const glow = 0.18 + Math.max(0, Math.sin(t * 4.8)) * 0.32;

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba("#FACC15", glow);
  ctx.beginPath();
  ctx.arc(x, y, r * 2.05, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#FDE047";
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#A16207";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "#64748B";
  ctx.fillRect(x - r * 0.5, y + r * 0.74, r, r * 0.72);
  ctx.restore();
}

function drawWave(ctx: Ctx, actor: any, alpha: number, t: number) {
  const x = actor.x;
  const y = actor.y;
  const size = Math.max(24, actor.size ?? 42);
  [0, 1, 2].forEach((i) => {
    drawWaveArc(
      ctx,
      x,
      y,
      size * (0.45 + i * 0.28),
      t * 0.2 + i * 0.08,
      alpha * (1 - i * 0.18),
      actor.color || C.arrow,
    );
  });
}

function drawLabelActor(ctx: Ctx, actor: any, alpha: number, t: number, W: number, H: number) {
  const text = String(actor.text || "").trim();
  const cx = actor.x;
  const cy = actor.y;
  const size = Math.max(18, (actor.fontSize || actor.size || 16) * 1.08);
  const compact = text.toLowerCase().replace(/\s+/g, "");

  if (/^(h2o|water)$/.test(compact)) {
    drawWaterDrop(ctx, cx, cy, size * 0.58, alpha, actor.color || C.water);
    return;
  }
  if (/^(co2|carbondioxide)$/.test(compact)) {
    drawCO2(ctx, cx, cy, size * 0.62, alpha);
    return;
  }
  if (/^(o2|oxygen)$/.test(compact)) {
    drawO2(ctx, cx, cy, size * 0.56, alpha);
    return;
  }
  if (/^(glucose|sugar|c6h)/.test(compact)) {
    drawGlucose(ctx, cx, cy, size * 0.64, alpha, t, actor.color || C.glucose);
    return;
  }
  if (/^(energy|bolt|lightning)$/.test(compact)) {
    drawBolt(ctx, cx, cy, size * 0.6, alpha, actor.color || C.bolt);
    return;
  }

  if (text.length >= 16) {
    drawEducationCard(
      ctx,
      W,
      H,
      text,
      alpha,
      t,
      actor.extra?.concept || actor.conceptTitle || "",
      actor.color || C.arrow,
    );
    return;
  }

  drawConceptPill(ctx, cx, cy, alpha, actor.color || C.arrow, text || "Concept");
}

function drawUnknownActor(ctx: Ctx, actor: any, alpha: number): void {
  drawConceptPill(
    ctx,
    actor.x,
    actor.y,
    alpha,
    actor.color || C.arrow,
    String(actor.type || "shape"),
  );
}

function clampToSafeArea(
  x: number,
  y: number,
  radius: number,
  type: string,
  W: number,
  H: number,
) {
  const marginX = Math.max(16, radius + 8);
  const minX = marginX;
  const maxX = W - marginX;

  const isSkyActor = type === "sun" || type === "cloud" || type === "oxygen" || type === "co2";
  const isGroundActor = type === "plant" || type === "root" || type === "rock" || type === "animal";
  const minY = Math.max(16, radius + 8);
  const maxY = isSkyActor
    ? H * 0.52
    : isGroundActor
      ? H - Math.max(18, radius * 0.4)
      : H - Math.max(14, radius + 6);

  return {
    x: clamp(x, minX, maxX),
    y: clamp(y, minY, maxY),
  };
}

function resolveActorSize(raw: any, type: string, W: number, H: number): number {
  const base = BASE_SIZE[type] ?? 42;
  const provided = toNumber(raw?.size);
  const source =
    provided == null
      ? base
      : Math.abs(provided) <= 1.2
        ? Math.abs(provided) * Math.min(W, H)
        : provided;
  const weighted = source * (IMPORTANCE[type] ?? 1);
  return clamp(weighted, 12, Math.min(W, H) * 0.42);
}

function ensureLineEndpoints(actor: any, W: number, H: number): any {
  if (actor.type !== "arrow" && actor.type !== "line" && actor.type !== "wire") return actor;
  const x1 = resolveAxis(actor.x1, W, actor.x);
  const y1 = resolveAxis(actor.y1, H, actor.y);
  const x2Raw = toNumber(actor.x2);
  const y2Raw = toNumber(actor.y2);
  const hasPointEnd = x2Raw != null && y2Raw != null;

  const lengthRaw = toNumber(actor.length);
  const length = lengthRaw == null
    ? Math.max(40, (BASE_SIZE[actor.type] ?? 42) * 2)
    : Math.abs(lengthRaw) <= 1.2
      ? Math.abs(lengthRaw) * Math.min(W, H)
      : Math.abs(lengthRaw);

  if (hasPointEnd) {
    return {
      ...actor,
      x1,
      y1,
      x2: resolveAxis(x2Raw, W, x1),
      y2: resolveAxis(y2Raw, H, y1),
      x: x1,
      y: y1,
    };
  }

  return {
    ...actor,
    x1,
    y1,
    x: x1,
    y: y1,
    length,
  };
}

function autoLayoutActors(actors: any[], W: number, H: number): PositionedActor[] {
  const counters = new Map<string, number>();
  const placed: PositionedActor[] = (actors || []).map((raw) => {
    const type = resolveType(raw?.type, raw?.text);
    const index = counters.get(type) ?? 0;
    counters.set(type, index + 1);

    const slot = defaultPoint(type, W, H);
    const ring = Math.floor(index / 2) + 1;
    const sign = index % 2 === 0 ? 1 : -1;
    const spreadX = index === 0 ? 0 : sign * ring * 44;
    const spreadY = index === 0 ? 0 : (sign > 0 ? 1 : -1) * ring * 18;

    const x = resolveAxis(raw?.x, W, slot.x + spreadX);
    const y = resolveAxis(raw?.y, H, slot.y + spreadY);
    const size = resolveActorSize(raw, type, W, H);
    const radius = Math.max(12, size * 0.45);
    const clamped = clampToSafeArea(x, y, radius, type, W, H);
    const importance = IMPORTANCE[type] ?? 1;
    const z = Number.isFinite(raw?.zIndex)
      ? Number(raw.zIndex)
      : (Z_LAYER[type] ?? 40) + Math.round(importance * 2);
    const explicitPos = toNumber(raw?.x) != null && toNumber(raw?.y) != null;

    return {
      ...raw,
      type,
      x: clamped.x,
      y: clamped.y,
      size,
      _radius: radius,
      _importance: importance,
      _z: z,
      _explicitPos: explicitPos,
    };
  });

  // Attach semantic dependents to the main plant anchor when backend omits positions.
  const mainPlant = placed
    .filter((actor) => actor.type === "plant")
    .sort((a, b) => b._importance - a._importance)[0];
  if (mainPlant) {
    let leafIndex = 0;
    let rootIndex = 0;
    placed.forEach((actor) => {
      if (actor._explicitPos) return;

      if (actor.type === "leaf") {
        const side = leafIndex % 2 === 0 ? -1 : 1;
        const ring = Math.floor(leafIndex / 2);
        actor.x = mainPlant.x + side * (26 + ring * 16);
        actor.y = mainPlant.y - (88 + ring * 12);
        leafIndex += 1;
      } else if (actor.type === "root") {
        const side = rootIndex % 2 === 0 ? -1 : 1;
        const ring = Math.floor(rootIndex / 2);
        actor.x = mainPlant.x + side * (10 + ring * 12);
        actor.y = Math.min(H * 0.9, mainPlant.y + 66 + ring * 9);
        actor._z = Math.min(actor._z, Z_LAYER.root ?? 26);
        rootIndex += 1;
      } else if (actor.type === "waterdrop" || actor.type === "water") {
        actor.x = mainPlant.x - 72;
        actor.y = Math.min(H * 0.88, mainPlant.y + 46);
      } else if (actor.type === "co2") {
        actor.x = Math.max(mainPlant.x + 130, W * 0.62);
        actor.y = mainPlant.y - 110;
      } else if (actor.type === "glucose") {
        actor.x = mainPlant.x + 78;
        actor.y = mainPlant.y - 94;
      } else if (actor.type === "oxygen") {
        actor.x = mainPlant.x + 86;
        actor.y = mainPlant.y - 160;
      }

      const clamped = clampToSafeArea(actor.x, actor.y, actor._radius, actor.type, W, H);
      actor.x = clamped.x;
      actor.y = clamped.y;
    });
  }

  // Push lower-importance actors away to avoid center piles — skip when all positions
  // were supplied by the rule engine (pixels > 1.2) so layout stays deterministic.
  const allExplicit = placed.length > 0 && placed.every((a) => a._explicitPos);
  if (!allExplicit) {
    for (let pass = 0; pass < 3; pass += 1) {
      for (let i = 0; i < placed.length; i += 1) {
        for (let j = i + 1; j < placed.length; j += 1) {
          const a = placed[i];
          const b = placed[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.0001;
          const minDist = a._radius + b._radius + 12;
          if (dist >= minDist) continue;

          const overlap = (minDist - dist) / minDist;
          const nx = dx / dist;
          const ny = dy / dist;
          const aWeight = 1 / Math.max(0.25, a._importance);
          const bWeight = 1 / Math.max(0.25, b._importance);
          const sum = aWeight + bWeight;
          const aPush = (overlap * 20 * aWeight) / sum;
          const bPush = (overlap * 20 * bWeight) / sum;

          a.x -= nx * aPush;
          a.y -= ny * aPush;
          b.x += nx * bPush;
          b.y += ny * bPush;

          const ac = clampToSafeArea(a.x, a.y, a._radius, a.type, W, H);
          const bc = clampToSafeArea(b.x, b.y, b._radius, b.type, W, H);
          a.x = ac.x;
          a.y = ac.y;
          b.x = bc.x;
          b.y = bc.y;
        }
      }
    }
  }

  return placed
    .map((actor) => ensureLineEndpoints(actor, W, H))
    .sort((a, b) => a._z - b._z);
}

function resolveMotion(
  actor: any,
  t: number,
  index: number,
  elapsedMs?: number,
  loopSlowMul = 1,
) {
  const raw = String(actor.animation || "idle").toLowerCase();
  const anim = raw.replace(/\s+/g, "");
  const phase = index * 0.72;
  let intensity = clamp(toNumber(actor.motionIntensity) ?? 1, 0.5, 1.8);
  intensity *= clamp(loopSlowMul, 0.68, 1.05);

  const holdUntil = Number(actor.motionHoldUntilMs ?? 0);
  const holdMul =
    holdUntil > 0 && elapsedMs != null && elapsedMs < holdUntil ? 0.18 : 1;

  const reactAt = Number(actor.reactAfterMs ?? 0);
  const canReact =
    actor.targetReaction === true &&
    reactAt > 0 &&
    elapsedMs != null &&
    elapsedMs >= reactAt;
  const reactionPulse = canReact ? 1 + 0.15 * Math.sin((elapsedMs - reactAt) * 0.0048) : 1;

  const statePulse =
    actor.stateChange === true &&
    reactAt > 0 &&
    elapsedMs != null &&
    elapsedMs >= reactAt
      ? 1 + 0.12 * Math.sin((elapsedMs - reactAt) * 0.0042)
      : 1;

  let dx = 0;
  let dy = 0;
  let scale = 1;
  let rotation = 0;
  let alphaMul = 1;

  if (anim === "flow") {
    dx = Math.sin((t + phase) * 1.05) * 7 * intensity;
    dy = Math.cos((t + phase) * 0.65) * 4 * intensity;
  } else if (anim === "rise" || anim === "bubbleup") {
    dy = (-11 - Math.sin((t + phase) * 1.35) * 8) * intensity;
    dx = Math.sin((t + phase) * 0.85) * 3.5 * intensity;
  } else if (anim === "fall") {
    dy = (11 + Math.abs(Math.sin((t + phase) * 1.45)) * 9) * intensity;
    dx = Math.sin((t + phase) * 0.55) * 3 * intensity;
    alphaMul = 0.9;
  } else if (anim === "transform") {
    scale = 1 + 0.09 * Math.sin((t + phase) * 2.3) * intensity;
    rotation = Math.sin((t + phase) * 1.05) * 0.07 * intensity;
  } else if (anim === "sway" || anim === "float") {
    dx = oscillate(t + phase, 1.1, -4, 4) * intensity;
    dy = oscillate(t + phase * 0.8, 0.7, -2.5, 2.5) * intensity;
  } else if (anim === "pulse" || anim === "glow" || anim === "shine") {
    scale = pulse(t + phase, 1.8, 0.055 * intensity, 1);
  } else if (anim === "floatin" || anim === "floatout" || anim === "absorb") {
    dy = oscillate(t + phase, 1.15, -10, 4) * intensity;
    dx = Math.sin((t + phase) * 0.95) * 4 * intensity;
  } else if (anim === "rotate" || anim === "spin") {
    rotation = (t + phase) * 0.55;
  } else if (anim === "bounce") {
    dy = -Math.abs(Math.sin((t + phase) * 2.6) * 9) * intensity;
  } else if (anim === "drift") {
    dx = Math.sin((t + phase) * 0.72) * 7 * intensity;
    dy = Math.sin((t + phase) * 0.48) * 5 * intensity;
  } else if (anim === "vibrate") {
    dx = Math.sin((t + phase) * 18) * 1.8 * intensity;
    dy = Math.cos((t + phase) * 20) * 1.5 * intensity;
  } else {
    dy = Math.sin((t + phase) * 0.6) * 1.8 * intensity;
  }

  dx *= holdMul;
  dy *= holdMul;
  if (actor.targetReaction === true && canReact) {
    scale *= reactionPulse;
  }
  if (actor.stateChange === true) {
    scale *= statePulse;
  }

  return { dx, dy, scale, rotation, alphaMul };
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const h = String(hex).replace("#", "").trim();
  if (h.length === 6) {
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
    };
  }
  return null;
}

function lerpColor(a: string, b: string, u: number): string {
  const A = hexToRgb(a);
  const B = hexToRgb(b);
  if (!A || !B) return b;
  const t = clamp01(u);
  const r = Math.round(lerp(A.r, B.r, t));
  const g = Math.round(lerp(A.g, B.g, t));
  const bl = Math.round(lerp(A.b, B.b, t));
  const hx = (n: number) => n.toString(16).padStart(2, "0");
  return `#${hx(r)}${hx(g)}${hx(bl)}`;
}

/** Before → after tint: primary (stateChange) or effect (targetReaction). */
function resolveActorColor(actor: any, elapsedMs: number): string {
  const base = String(actor.color ?? "#FFFFFF");
  const active = actor.colorActive ?? actor.colorReact;
  const ra = Number(actor.reactAfterMs ?? 0);
  const eligible =
    Boolean(active) &&
    ra > 0 &&
    (actor.targetReaction === true ||
      actor.stateChange === true ||
      actor.showStateChange === true);
  if (!eligible || elapsedMs < ra) return base;
  return lerpColor(base, String(active), clamp01((elapsedMs - ra) / 560));
}

export const ACTOR_RENDERERS: Record<string, DrawFn> = {
  arrow: (ctx, actor, alpha) => {
    if (typeof actor.x2 === "number" && typeof actor.y2 === "number") {
      const dx = actor.x2 - actor.x;
      const dy = actor.y2 - actor.y;
      drawArrow(
        ctx,
        actor.x,
        actor.y,
        Math.atan2(dy, dx),
        Math.sqrt(dx * dx + dy * dy),
        actor.color || C.arrow,
        actor.thickness ?? 3.2,
        alpha,
      );
      return;
    }
    drawArrow(
      ctx,
      actor.x,
      actor.y,
      actor.angle ?? 0,
      actor.length ?? 120,
      actor.color || C.arrow,
      actor.thickness ?? 3.2,
      alpha,
    );
  },

  line: (ctx, actor, alpha) => {
    const x1 = actor.x1 ?? actor.x;
    const y1 = actor.y1 ?? actor.y;
    const x2 = actor.x2 ?? x1 + 120;
    const y2 = actor.y2 ?? y1;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = actor.color || C.arrow;
    ctx.lineWidth = actor.thickness ?? 2.6;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  },

  wire: (ctx, actor, alpha, _t, W, H) => {
    if (typeof actor.x2 === "number" && typeof actor.y2 === "number") {
      ACTOR_RENDERERS.line(ctx, actor, alpha, 0, W, H);
      return;
    }
    const w = Math.max(120, (actor.length ?? Math.min(W, H) * 0.46));
    const h = Math.max(70, w * 0.44);
    drawWireLoop(ctx, actor.x - w * 0.5, actor.y - h * 0.5, w, h, alpha, actor.color || "#FACC15");
  },

  sun: (ctx, actor, alpha, t) => drawSol(ctx, actor.x, actor.y, actor.size ?? 52, t, alpha),
  cloud: (ctx, actor, alpha) => drawCloud(ctx, actor.x, actor.y, (actor.size ?? 52) / 24, alpha),
  plant: (ctx, actor, alpha, t) => drawSunny(ctx, actor.x, actor.y, t, true, (actor.size ?? 104) / 104, alpha),
  leaf: (ctx, actor, alpha) => drawLeafGlyph(ctx, actor, alpha),
  root: (ctx, actor, alpha) => drawRootGlyph(ctx, actor, alpha),
  waterdrop: (ctx, actor, alpha) =>
    drawWaterDrop(ctx, actor.x, actor.y, (actor.size ?? 34) * 0.5, alpha, actor.color || C.water),
  water: (ctx, actor, alpha) =>
    drawWaterDrop(ctx, actor.x, actor.y, (actor.size ?? 34) * 0.5, alpha, actor.color || C.water),
  co2: (ctx, actor, alpha) => drawCO2(ctx, actor.x, actor.y, (actor.size ?? 36) * 0.52, alpha),
  glucose: (ctx, actor, alpha, t) =>
    drawGlucose(ctx, actor.x, actor.y, (actor.size ?? 40) * 0.55, alpha, t, actor.color || C.glucose),
  bolt: (ctx, actor, alpha) =>
    drawBolt(ctx, actor.x, actor.y, (actor.size ?? 38) * 0.55, alpha, actor.color || C.bolt),
  oxygen: (ctx, actor, alpha) => drawO2(ctx, actor.x, actor.y, (actor.size ?? 30) * 0.55, alpha),
  rock: (ctx, actor, alpha) =>
    drawRock(ctx, actor.x, actor.y, (actor.size ?? 44) * 0.52, alpha, actor.color || C.rock),
  planet: (ctx, actor, alpha) =>
    drawPlanet(ctx, actor.x, actor.y, (actor.size ?? 48) * 0.55, alpha, actor.color || "#42A5F5"),
  volcano: (ctx, actor, alpha) => drawVolcano(ctx, actor.x, actor.y, actor.size ?? 62, alpha),
  ocean: (ctx, actor, alpha) => {
    const x = actor.x;
    const y = actor.y;
    const w = Math.max(48, (actor.size ?? 80) * 1.1);
    const h = Math.max(22, (actor.size ?? 80) * 0.28);
    ctx.save();
    ctx.globalAlpha = alpha * 0.88;
    const g = ctx.createLinearGradient(x - w * 0.5, y - h, x + w * 0.5, y + h);
    g.addColorStop(0, actor.color || "#1976D2");
    g.addColorStop(1, "#0D47A1");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x, y, w * 0.52, h * 0.85, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x - w * 0.12, y, w * 0.35, 0.3, Math.PI - 0.3);
    ctx.stroke();
    ctx.restore();
  },
  mountain: (ctx, actor, alpha) =>
    drawRock(ctx, actor.x, actor.y - (actor.size ?? 70) * 0.08, (actor.size ?? 70) * 0.52, alpha, actor.color || "#6D4C41"),
  thermometer: (ctx, actor, alpha) =>
    drawThermometer(ctx, actor.x, actor.y, actor.size ?? 1, alpha, actor.temp ?? 0.5),
  molecule: (ctx, actor, alpha, t, W, H) => {
    const mt = String(actor.moleculeType || actor.extra?.moleculeType || "").toLowerCase();
    if (mt.includes("co2")) return ACTOR_RENDERERS.co2(ctx, actor, alpha, t, W, H);
    if (mt.includes("oxygen") || mt === "o2") return ACTOR_RENDERERS.oxygen(ctx, actor, alpha, t, W, H);
    if (mt.includes("glucose") || mt.includes("sugar")) return ACTOR_RENDERERS.glucose(ctx, actor, alpha, t, W, H);
    return ACTOR_RENDERERS.waterdrop(ctx, actor, alpha, t, W, H);
  },
  bulb: (ctx, actor, alpha, t) => drawBulb(ctx, actor, alpha, t),
  ear: (ctx, actor, alpha) => drawSimpleEar(ctx, actor, alpha),
  battery: (ctx, actor, alpha) => drawBattery(ctx, actor.x, actor.y, (actor.size ?? 50) / 50, alpha),
  switch: (ctx, actor, alpha) =>
    drawSwitch(ctx, actor.x, actor.y, (actor.size ?? 44) / 44, alpha, actor.closed ?? true),
  wave: (ctx, actor, alpha, t) => drawWave(ctx, actor, alpha, t),

  label: (ctx, actor, alpha, t, W, H) => drawLabelActor(ctx, actor, alpha, t, W, H),

  animal: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, actor.label || "Animal"),
  rabbit: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Herbivore"),
  deer: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Herbivore"),
  goat: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Herbivore"),
  lion: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Carnivore"),
  fox: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Carnivore"),
  snake: (ctx, actor, alpha) => drawFallbackAnimal(ctx, actor, alpha, "Predator"),
  bird: (ctx, actor, alpha, t) => {
    const x = actor.x;
    const y = actor.y;
    const s = Math.max(16, (actor.size ?? 36) * 0.45);
    const flap = Math.sin(t * 9) * 5.2;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = actor.color || "#374151";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x - s, y);
    ctx.quadraticCurveTo(x - s * 0.4, y - s - flap, x, y);
    ctx.quadraticCurveTo(x + s * 0.4, y - s - flap, x + s, y);
    ctx.stroke();
    ctx.restore();
  },
};

/**
 * Run the same auto-layout used for drawing. Call this before flow-line mapping
 * so scene.animations[] endpoints match on-screen actor centers.
 */
export function layoutActorsForScene(actors: any[], W: number, H: number): PositionedActor[] {
  return autoLayoutActors(actors || [], W, H);
}

/** Render actors after layout — use with layoutActorsForScene for flow-line alignment. */
export function renderLaidOutActors(
  laidOut: PositionedActor[],
  ctx: Ctx,
  elapsedMs: number,
  W: number,
  H: number,
  options?: RenderLaidOutActorsOptions,
): number {
  const ve = options?.visualElapsedMs ?? elapsedMs;
  const t = ve * 0.001;
  const stagger = clamp(150 - laidOut.length * 4, 70, 150);
  let drawn = 0;
  const fid = options?.focusActorId ? String(options.focusActorId) : "";
  const multi = fid.length > 0 && laidOut.length > 1;

  const seg = options?.loopSegmentMs ?? 0;
  const tail = options?.segmentTailPauseMs ?? 0;
  let tailMul = 1;
  if (seg > 0 && tail > 0) {
    const pos = ((ve % seg) + seg) % seg;
    if (pos >= seg - tail) tailMul = 0.22;
  }

  const loopIdx = Math.max(0, options?.loopIndex ?? 0);
  const loopSlowMul = Math.max(0.72, 1 - loopIdx * 0.068);
  const glowRamp = 1 + loopIdx * 0.13;

  laidOut.forEach((actor, index) => {
    const delay = index * stagger;
    const baseAlpha = fadeIn(ve, delay, 640);
    const timelineAlpha = computeTimelineAlpha(actor, ve, baseAlpha);
    const motion = resolveMotion(actor, t, index, ve, loopSlowMul);
    motion.dx *= tailMul;
    motion.dy *= tailMul;
    let dim = 1;
    if (multi && String(actor.id ?? "") !== fid) {
      dim = 0.18;
      const ra = Number(actor.reactAfterMs ?? 0);
      if (actor.targetReaction && ra > 0 && ve >= ra + 100) {
        dim = Math.min(1, 0.18 + 0.7 * clamp01((ve - ra - 100) / 520));
      }
    }
    const alpha = clamp01(timelineAlpha * motion.alphaMul * dim);
    if (alpha <= 0.004) return;

    const entry = clamp01((ve - delay) / 620);
    const lift = (1 - entry) * 14;
    const scaleIn = 0.94 + entry * 0.06;
    const draw = ACTOR_RENDERERS[actor.type] ?? drawUnknownActor;

    const isFocus = Boolean(fid && String(actor.id ?? "") === fid);
    const raState = Number(actor.reactAfterMs ?? 0);
    const hasTeachingState =
      raState > 0 &&
      (actor.stateChange === true ||
        actor.targetReaction === true ||
        actor.showStateChange === true);
    let stateScaleMul = 1;
    if (hasTeachingState) {
      if (ve < raState) stateScaleMul = 0.9;
      else stateScaleMul = 1.02 + 0.04 * clamp01((ve - raState) / 450);
    }
    const emphasisScale =
      (isFocus ? 1.2 : String(actor.emphasis || "").toLowerCase() === "secondary" ? 0.92 : 1) *
      stateScaleMul;

    const resolvedColor = resolveActorColor(actor, ve);

    const transformedActor = {
      ...actor,
      color: resolvedColor,
      x: actor.x + motion.dx,
      y: actor.y + motion.dy + lift,
      size: (actor.size ?? 40) * motion.scale * scaleIn * emphasisScale,
    };

    const ringR = (actor._radius ?? 24) + 12;
    const pastState = hasTeachingState && ve >= raState;
    const glowStrength = pastState ? glowRamp * (1 + 0.22 * clamp01((ve - raState) / 600)) : 0;

    if (isFocus) {
      ctx.save();
      ctx.globalAlpha = alpha * 0.42;
      ctx.strokeStyle = "rgba(255,255,255,0.92)";
      ctx.lineWidth = 2.5;
      ctx.setLineDash?.([7, 6]);
      ctx.beginPath();
      ctx.arc(transformedActor.x, transformedActor.y, ringR, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash?.([]);
      ctx.restore();
    }

    ctx.save();
    if (motion.rotation) {
      ctx.translate(transformedActor.x, transformedActor.y);
      ctx.rotate(motion.rotation);
      ctx.translate(-transformedActor.x, -transformedActor.y);
    }
    draw(ctx, transformedActor, alpha, t, W, H);
    ctx.restore();

    if (pastState && glowStrength > 0 && actor.type !== "label") {
      ctx.save();
      const pulse = 1 + 0.06 * Math.sin(ve * 0.0033);
      ctx.globalAlpha = alpha * 0.28 * Math.min(1.15, glowStrength);
      ctx.strokeStyle = resolvedColor;
      ctx.lineWidth = 2.2 + loopIdx * 0.35;
      ctx.beginPath();
      ctx.arc(
        transformedActor.x,
        transformedActor.y,
        ringR * pulse * (1.05 + loopIdx * 0.04),
        0,
        Math.PI * 2,
      );
      ctx.stroke();
      ctx.globalAlpha = alpha * 0.12 * Math.min(1.1, glowStrength);
      ctx.fillStyle = resolvedColor;
      ctx.beginPath();
      ctx.arc(
        transformedActor.x,
        transformedActor.y,
        ringR * pulse * 1.35 * (1.04 + loopIdx * 0.05),
        0,
        Math.PI * 2,
      );
      ctx.fill();
      ctx.restore();
    }
    drawn += 1;
  });

  return drawn;
}

export function renderActors(
  actors: any[],
  ctx: Ctx,
  elapsedMs: number,
  W: number,
  H: number,
): number {
  return renderLaidOutActors(layoutActorsForScene(actors, W, H), ctx, elapsedMs, W, H);
}
