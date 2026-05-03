/**
 * animation/domains/water_cycle.ts
 * Water cycle with full scene anchors. Rewritten to remove broken Shapes.drawWaterDropsRising/drawFallingRain.
 */
import { C, drawArrow, drawCloud, drawSol, drawWaterDrop } from "../core/shapes";
import { fadeIn, easeOut, clamp01, lerp } from "../core/easing";

type Ctx = any;

export const keywords = [
  "water cycle",
  "evaporation",
  "condensation",
  "precipitation",
  "transpiration",
  "runoff",
];

export function drawBackground(
  ctx: Ctx,
  W: number,
  H: number,
) {
  const sky = ctx.createLinearGradient(0, 0, 0, H * 0.58);
  sky.addColorStop(0, C.skyTop);
  sky.addColorStop(1, C.skyBottom);
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, H * 0.58);

  // Ocean / water body
  const ocean = ctx.createLinearGradient(0, H * 0.58, 0, H);
  ocean.addColorStop(0, "#1565C0");
  ocean.addColorStop(1, "#0D47A1");
  ctx.fillStyle = ocean;
  ctx.fillRect(0, H * 0.58, W, H * 0.42);

  // Ground stripe
  ctx.fillStyle = C.soilTop;
  ctx.fillRect(0, H * 0.56, W, H * 0.04);
  ctx.fillStyle = C.grass;
  ctx.fillRect(0, H * 0.56, W, 12);

  // Ambient clouds
  drawCloud(ctx, W * 0.18, H * 0.1, 1.1, 0.72);
  drawCloud(ctx, W * 0.82, H * 0.14, 0.88, 0.62);
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
) {
  drawSol(ctx, W * 0.2, H * 0.25, 56, t, 1);
  drawCloud(ctx, W * 0.55, H * 0.22, 1.1, 0.88 + Math.sin(t * 0.03) * 0.06);
}

export function keywordFallback(
  ctx: Ctx,
  sceneText: string,
  elapsed: number,
  _t: number,
  W: number,
  H: number,
) {
  const txt = sceneText.toLowerCase();

  if (/evapor/.test(txt)) {
    // Water drops rising upward
    [0, 280, 560].forEach((delay, i) => {
      const rise = easeOut(clamp01((elapsed - delay) / 2000));
      drawWaterDrop(
        ctx,
        W * 0.33 + i * 30,
        lerp(H * 0.56, H * 0.18, rise),
        14,
        fadeIn(elapsed, delay, 400),
      );
    });
    return;
  }

  if (/cloud|condense|vapor/.test(txt)) {
    const a = fadeIn(elapsed, 200, 800);
    drawCloud(ctx, W * 0.5, H * 0.18, 1.3, a * 0.9);
    drawCloud(ctx, W * 0.68, H * 0.12, 1.0, a * 0.75);
    return;
  }

  if (/rain|precipit|fall/.test(txt)) {
    [280, 330, 365, 410, 455].forEach((rx, i) => {
      const fall = easeOut(clamp01((elapsed - i * 180) / 1800));
      const ry = lerp(H * 0.25, H * 0.56, fall);
      const a = fadeIn(elapsed, i * 180, 400);
      ctx.save();
      ctx.globalAlpha = a;
      ctx.fillStyle = "#42A5F5";
      ctx.beginPath();
      ctx.moveTo(rx, ry - 10);
      ctx.lineTo(rx + 4, ry + 5);
      ctx.lineTo(rx - 4, ry + 5);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    });
    return;
  }

  // Default: show the full cycle arrow
  const a = fadeIn(elapsed, 400, 700);
  drawArrow(ctx, W * 0.25, H * 0.44, -Math.PI / 2, H * 0.24 * a, "#0288D1", 3, a);
  drawWaterDrop(ctx, W * 0.36, H * 0.56, 14, a);
}
