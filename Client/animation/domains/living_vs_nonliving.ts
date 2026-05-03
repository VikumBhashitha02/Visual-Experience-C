/**
 * domains/living_vs_nonliving.ts — Background, anchors, and keyword fallback.
 * Rewritten to use only functions that exist in shapes.ts.
 */

import { C, drawArrow, drawRock, drawSol, drawSunny, drawWaterDrop } from "../core/shapes";
import { fadeIn } from "../core/easing";

type Ctx = any;

export const keywords = [
  "living things",
  "non-living",
  "living organisms",
  "growth",
  "environment",
  "components",
  "living world",
  "organisms",
];

export function drawBackground(ctx: Ctx, W: number, H: number): void {
  const sk = ctx.createLinearGradient(0, 0, 0, H * 0.58);
  sk.addColorStop(0, C.skyTop);
  sk.addColorStop(1, C.skyBottom);
  ctx.fillStyle = sk;
  ctx.fillRect(0, 0, W, H * 0.58);

  ctx.fillStyle = C.grass;
  ctx.fillRect(0, H * 0.58, W * 0.5, H * 0.42);
  ctx.fillStyle = C.soilTop;
  ctx.fillRect(W * 0.5, H * 0.58, W * 0.5, H * 0.42);
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
): void {
  drawSunny(ctx, W * 0.28, H * 0.65, t, false, 0.85, 1);
  drawRock(ctx, W * 0.72, H * 0.72, 40, 1, "#9E9E9E");
  drawSol(ctx, W * 0.5, H * 0.22, 48, t, 0.85);
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

  if (/growth|living|organism|plant/.test(txt)) {
    const a = fadeIn(elapsed, 200, 700);
    drawSunny(ctx, W * 0.35, H * 0.65, t, false, 1.2, a);
    const arrA = fadeIn(elapsed, 600, 500);
    drawArrow(ctx, W * 0.35, H * 0.44, -Math.PI / 2, H * 0.14 * arrA, C.arrow, 3, arrA);
    return;
  }

  if (/water|drink|need/.test(txt)) {
    const a = fadeIn(elapsed, 200, 700);
    drawWaterDrop(ctx, W * 0.5, H * 0.45, 24, a);
    return;
  }

  // default non-living (rock)
  const a = fadeIn(elapsed, 300, 800);
  drawRock(ctx, W * 0.65, H * 0.65, 42, a, "#9E9E9E");
  drawRock(ctx, W * 0.3, H * 0.7, 30, a * 0.8, "#9E9E9E");
}
