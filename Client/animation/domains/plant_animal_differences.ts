/**
 * domains/plant_animal_differences.ts — Background, anchors, and keyword fallback.
 * Rewritten to use only functions that exist in shapes.ts.
 */

import {
  C,
  drawArrow,
  drawBolt,
  drawRock,
  drawSunny,
  drawWaterDrop,
} from "../core/shapes";
import { fadeIn } from "../core/easing";

type Ctx = any;

export const keywords = [
  "differences between plants and animals",
  "cell wall",
  "chlorophyll",
  "autotrophic vs heterotrophic",
  "plant characteristics",
  "animal characteristics",
];

export function drawBackground(ctx: Ctx, W: number, H: number): void {
  const sk = ctx.createLinearGradient(0, 0, 0, H * 0.6);
  sk.addColorStop(0, C.skyTop);
  sk.addColorStop(1, C.skyBottom);
  ctx.fillStyle = sk;
  ctx.fillRect(0, 0, W, H * 0.6);
  // Left side: green garden
  ctx.fillStyle = C.grass;
  ctx.fillRect(0, H * 0.6, W * 0.5, H * 0.4);
  // Right side: sandy ground
  ctx.fillStyle = "#D4A17A";
  ctx.fillRect(W * 0.5, H * 0.6, W * 0.5, H * 0.4);
  // Divider
  ctx.strokeStyle = "#475569";
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.moveTo(W * 0.5, H * 0.2);
  ctx.lineTo(W * 0.5, H * 0.95);
  ctx.stroke();
  // Labels
  ctx.fillStyle = "#1E3A8A";
  ctx.font = "bold 13px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("PLANT", W * 0.25, H * 0.15);
  ctx.fillStyle = "#7C2D12";
  ctx.fillText("ANIMAL", W * 0.75, H * 0.15);
}

function _drawSimpleAnimal(ctx: Ctx, cx: number, cy: number, scale: number, t: number, alpha: number): void {
  const s = Math.max(0.3, scale);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#D2691E";
  ctx.beginPath(); ctx.ellipse(cx, cy, 22 * s, 14 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(cx + 20 * s, cy - 6 * s, 10 * s, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = "#8B4513"; ctx.lineWidth = 2.5 * s; ctx.lineCap = "round";
  const step = Math.sin(t * 3) * 4 * s;
  [[cx - 8, step], [cx, -step], [cx + 6, step]].forEach(([lx, dy]) => {
    ctx.beginPath(); ctx.moveTo(lx as number, cy + 10 * s); ctx.lineTo(lx as number, cy + 22 * s + (dy as number)); ctx.stroke();
  });
  ctx.restore();
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
): void {
  drawSunny(ctx, W * 0.25, H * 0.68, t, true, 1, 1);
  _drawSimpleAnimal(ctx, W * 0.75, H * 0.68, 1.05, t, 1);
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
  if (/plant|chlorophyll|autotrophic|photosynthesis/.test(txt)) {
    drawSunny(ctx, W * 0.28, H * 0.68, t, true, 1.3, a);
    const arrowA = fadeIn(elapsed, 600, 500);
    drawArrow(ctx, W * 0.28, H * 0.46, -Math.PI / 2, H * 0.16 * arrowA, "#4CAF50", 3, arrowA);
    drawWaterDrop(ctx, W * 0.16, H * 0.7, 14, arrowA);
    return;
  }
  if (/animal|heterotrophic|eat|move|locomotion/.test(txt)) {
    _drawSimpleAnimal(ctx, W * 0.5, H * 0.6, 1.4, t, a);
    const arrA = fadeIn(elapsed, 700, 500);
    drawArrow(ctx, W * 0.3, H * 0.6, 0, W * 0.22 * arrA, "#EF6C00", 4, arrA);
    drawBolt(ctx, W * 0.68, H * 0.54, 20, arrA, "#EF6C00");
    return;
  }
  // Default: both sides
  drawSunny(ctx, W * 0.25, H * 0.68, t, true, 1, a);
  _drawSimpleAnimal(ctx, W * 0.75, H * 0.68, 1.0, t, a);
  drawArrow(ctx, W * 0.48, H * 0.46, 0, W * 0.04, "#475569", 2, a * 0.5);
  drawArrow(ctx, W * 0.52, H * 0.46, Math.PI, W * 0.04, "#475569", 2, a * 0.5);
}
