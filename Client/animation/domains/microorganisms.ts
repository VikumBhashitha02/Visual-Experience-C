/**
 * domains/microorganisms.ts — Background, anchors, and keyword fallback.
 * Rewritten to use only functions that exist in shapes.ts.
 */

import { C, drawBolt, drawWaterDrop } from "../core/shapes";
import { fadeIn } from "../core/easing";
import { rgba } from "../core/easing";

type Ctx = any;

export const keywords = [
  "micro-organisms",
  "microorganism",
  "bacteria",
  "fungi",
  "algae",
  "microscope",
  "pond water",
  "tiny organisms",
  "yeast",
  "virus",
];

// Draw a simple blob organism using inline canvas
function _drawBlob(ctx: Ctx, cx: number, cy: number, r: number, t: number, alpha: number, color = "#4CAF50"): void {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba(color, 0.5);
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  const wobble = 1 + Math.sin(t * 2.5) * 0.08;
  ctx.beginPath();
  ctx.ellipse(cx, cy, r * wobble, r * (2 - wobble), t * 0.3, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  // nucleus
  ctx.fillStyle = rgba(color, 0.7);
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.35, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

export function drawBackground(ctx: Ctx, W: number, H: number): void {
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#1e2937";
  ctx.beginPath();
  ctx.arc(W / 2, H / 2, Math.min(W, H) * 0.42, 0, Math.PI * 2);
  ctx.fill();
  // microscope crosshair
  ctx.strokeStyle = rgba("#60A5FA", 0.15);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(W * 0.5, H * 0.08); ctx.lineTo(W * 0.5, H * 0.92);
  ctx.moveTo(W * 0.08, H * 0.5); ctx.lineTo(W * 0.92, H * 0.5);
  ctx.stroke();
  ctx.strokeStyle = rgba("#60A5FA", 0.18);
  ctx.beginPath();
  ctx.arc(W * 0.5, H * 0.5, Math.min(W, H) * 0.42, 0, Math.PI * 2);
  ctx.stroke();
}

export function drawAnchorCharacters(
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
): void {
  drawWaterDrop(ctx, W * 0.5, H * 0.52, 88, 0.22, "#29B6F6");
  const bob = Math.sin(t * 0.18) * 5;
  _drawBlob(ctx, W * 0.38, H * 0.48 + bob, 18, t, 0.9, "#66BB6A");
  _drawBlob(ctx, W * 0.62, H * 0.55 - bob * 0.7, 14, t, 0.85, "#CE93D8");
  _drawBlob(ctx, W * 0.5, H * 0.4, 11, t * 0.8, 0.8, "#4FC3F7");
}

export function keywordFallback(
  ctx: Ctx,
  sceneText: string,
  elapsed: number,
  t: number,
  W: number,
  H: number,
): void {
  const a = fadeIn(elapsed, 200, 700);
  drawWaterDrop(ctx, W * 0.5, H * 0.52, 106, a * 0.28, "#29B6F6");
  const bob = Math.sin(t * 0.2) * 4;
  _drawBlob(ctx, W * 0.42, H * 0.47 + bob, 22, t, a, "#66BB6A");
  _drawBlob(ctx, W * 0.58, H * 0.56 - bob * 0.6, 18, t, a * 0.9, "#CE93D8");
  drawBolt(ctx, W * 0.5, H * 0.32, 14, fadeIn(elapsed, 700, 500), "#60A5FA");
}
