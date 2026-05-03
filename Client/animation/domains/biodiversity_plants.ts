/**
 * domains/biodiversity_plants.ts — Background, anchors, and keyword fallback.
 * Rewritten to use only functions that exist in shapes.ts.
 */

import { C, drawArrow, drawRock, drawSol, drawSunny, drawWaterDrop } from "../core/shapes";
import { fadeIn } from "../core/easing";

type Ctx = any;

export const keywords = [
  "diversity of plants",
  "trees",
  "shrubs",
  "creepers",
  "flowering",
  "non-flowering",
  "habitat",
  "terrestrial",
  "aquatic",
  "mangrove",
  "plant diversity",
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
  // small water pond on right
  ctx.fillStyle = "#1565C0";
  ctx.beginPath();
  ctx.ellipse(W * 0.8, H * 0.78, W * 0.12, H * 0.06, 0, 0, Math.PI * 2);
  ctx.fill();
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
): void {
  // Three progressively smaller plant types
  drawSunny(ctx, W * 0.18, H * 0.68, t, false, 1.4, 1);   // tall tree (large plant)
  drawSunny(ctx, W * 0.42, H * 0.72, t * 0.9, false, 0.9, 0.9); // medium shrub
  drawSunny(ctx, W * 0.62, H * 0.74, t * 0.7, false, 0.6, 0.82); // small creeper
  // Aquatic: water drop in pond
  drawWaterDrop(ctx, W * 0.8, H * 0.78, 18, 0.8, "#4FC3F7");
  drawSol(ctx, W * 0.88, H * 0.14, 36, t, 0.82);
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

  if (/tree|tall|terrestrial/.test(txt)) {
    drawSunny(ctx, W * 0.5, H * 0.66, t, false, 1.5, a);
    return;
  }
  if (/shrub|small|bush/.test(txt)) {
    drawSunny(ctx, W * 0.4, H * 0.7, t * 0.8, false, 0.9, a);
    drawSunny(ctx, W * 0.6, H * 0.72, t * 0.7, false, 0.75, a * 0.85);
    return;
  }
  if (/aquatic|water|lily|pond/.test(txt)) {
    ctx.save(); ctx.globalAlpha = a;
    ctx.fillStyle = "#1565C0";
    ctx.beginPath(); ctx.ellipse(W * 0.5, H * 0.7, W * 0.18, H * 0.08, 0, 0, Math.PI * 2);
    ctx.fill(); ctx.restore();
    drawWaterDrop(ctx, W * 0.5, H * 0.7, 22, a, "#4FC3F7");
    return;
  }

  // Default: all 3 types
  drawSunny(ctx, W * 0.22, H * 0.68, t, false, 1.3, a);
  drawSunny(ctx, W * 0.5, H * 0.72, t * 0.7, false, 0.85, a * 0.9);
  drawRock(ctx, W * 0.76, H * 0.7, 22, a * 0.8, "#9CA3AF");
  drawArrow(ctx, W * 0.34, H * 0.62, 0, W * 0.14, "#4CAF50", 2, a * 0.6);
}
