/**
 * domains/reproduction.ts — Background, anchors, and keyword fallback.
 * Rewritten to use only functions that exist in shapes.ts.
 */

import { C, drawArrow, drawBolt, drawSol, drawSunny, drawWaterDrop } from "../core/shapes";
import { easeOut, clamp01, fadeIn, lerp } from "../core/easing";

type Ctx = any;

export const keywords = [
  "reproduction",
  "offspring",
  "new organism",
  "seed",
  "egg",
  "budding",
  "vegetative reproduction",
  "asexual",
  "sexual reproduction",
];

export function drawBackground(ctx: Ctx, W: number, H: number): void {
  const sk = ctx.createLinearGradient(0, 0, 0, H * 0.6);
  sk.addColorStop(0, C.skyTop);
  sk.addColorStop(1, C.skyBottom);
  ctx.fillStyle = sk;
  ctx.fillRect(0, 0, W, H * 0.6);
  ctx.fillStyle = C.soilTop;
  ctx.fillRect(0, H * 0.6, W, H * 0.4);
  ctx.fillStyle = C.grass;
  ctx.fillRect(0, H * 0.6, W, 16);
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
): void {
  // Parent plant (large)
  drawSunny(ctx, W * 0.35, H * 0.68, t, true, 1.3, 1);
  // Baby sprouts (small versions)
  drawSunny(ctx, W * 0.58, H * 0.72, t * 0.7, false, 0.65, 0.85);
  drawSunny(ctx, W * 0.72, H * 0.74, t * 0.55, false, 0.5, 0.7);
  drawSol(ctx, W * 0.82, H * 0.14, 32, t, 0.75);
}

export function keywordFallback(
  ctx: Ctx,
  sceneText: string,
  elapsed: number,
  t: number,
  W: number,
  H: number,
): void {
  const txt = sceneText.toLowerCase();
  const a = fadeIn(elapsed, 200, 700);

  if (/seed|germination|sprout/.test(txt)) {
    // Seed on ground, then growth arrow
    const grow = easeOut(clamp01((elapsed - 400) / 2000));
    ctx.save(); ctx.globalAlpha = a;
    ctx.fillStyle = "#8D6E63";
    ctx.beginPath(); ctx.ellipse(W * 0.5, H * 0.64, 10, 7, 0, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    const sproutA = fadeIn(elapsed, 400, 800);
    drawSunny(ctx, W * 0.5, H * 0.64, t, false, 0.2 + grow * 0.8, sproutA);
    return;
  }

  if (/egg|young|hatch/.test(txt)) {
    // Egg shape
    const a2 = fadeIn(elapsed, 200, 700);
    ctx.save(); ctx.globalAlpha = a2;
    ctx.fillStyle = "#FFF9C4"; ctx.strokeStyle = "#F59E0B"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(W * 0.4, H * 0.52, 24, 30, 0, 0, Math.PI * 2);
    ctx.fill(); ctx.stroke();
    ctx.restore();
    const arrowA = fadeIn(elapsed, 800, 600);
    drawArrow(ctx, W * 0.46, H * 0.52, 0, W * 0.12 * arrowA, "#F59E0B", 3, arrowA);
    const hatchA = fadeIn(elapsed, 1000, 600);
    drawBolt(ctx, W * 0.66, H * 0.5, 18, hatchA, "#F59E0B");
    return;
  }

  // Default: parent → offspring
  drawSunny(ctx, W * 0.35, H * 0.65, t, true, 1.3, a);
  const arrowA = fadeIn(elapsed, 600, 500);
  drawArrow(ctx, W * 0.48, H * 0.63, 0, W * 0.22 * arrowA, "#4CAF50", 3, arrowA);
  const offA = fadeIn(elapsed, 900, 600);
  drawSunny(ctx, W * 0.68, H * 0.7, t * 0.6, false, 0.7, offA);
}
