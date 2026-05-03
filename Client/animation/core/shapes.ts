/**
 * animation/core/shapes.ts
 * Primitive drawing helpers used by actor and scene renderers.
 * All functions required by domain files are present here.
 */

import { lerp, pulse, rgba } from "./easing";

export type Ctx = CanvasRenderingContext2D | any;

const TAU = Math.PI * 2;

// ── Colour palette ────────────────────────────────────────────────────────────
export const C = {
  // Sky / backgrounds
  skyTop: "#B6DDFF",
  skyBottom: "#EEF7FF",
  skyBot: "#EEF7FF",        // alias used by older domain files
  space: "#0A0E1A",

  // Ground / vegetation
  soilTop: "#8D6E63",
  soilBottom: "#5D4037",
  ground: "#8D6E63",        // alias used by older domain files
  grass: "#59B45E",

  // Sun / light
  sunCore: "#FFE16C",
  sunEdge: "#FB8C00",
  ray: "#FBCB58",

  // Plant
  plantStem: "#6D4C41",
  leafMain: "#53B55F",
  leafDark: "#2E7D32",
  leafDk: "#2E7D32",        // alias
  leafHL: "#A5D6A7",        // leaf highlight colour

  // Water
  water: "#33B8F9",
  waterDark: "#0288D1",

  // Molecules
  co2Fill: "#D6E0E4",
  co2Stroke: "#6A8591",
  glucose: "#FF9A43",
  glucoseStroke: "#D35A00",
  hexFill: "#FF9A43",       // alias for glucose hex fill
  oxygenFill: "#DCF7E1",
  oxygenStroke: "#2E7D32",

  // Effects
  bolt: "#8B5CF6",
  rock: "#7C665F",
  rockDark: "#5D4037",

  // UI / arrows
  arrow: "#1D4ED8",
  arrowDef: "#1D4ED8",      // alias used in older domain files
  cardText: "#0F172A",
  white: "#FFFFFF",
  panelShadow: "#0F172A",

  // Circuit
  circuitBody: "#334155",
  circuitAccent: "#FACC15",
};

// ── Internal utils ─────────────────────────────────────────────────────────────
function beginRoundedRect(
  ctx: Ctx,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.max(0, Math.min(r, w * 0.5, h * 0.5));
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + w - radius, y);
  ctx.arcTo(x + w, y, x + w, y + radius, radius);
  ctx.lineTo(x + w, y + h - radius);
  ctx.arcTo(x + w, y + h, x + w - radius, y + h, radius);
  ctx.lineTo(x + radius, y + h);
  ctx.arcTo(x, y + h, x, y + h - radius, radius);
  ctx.lineTo(x, y + radius);
  ctx.arcTo(x, y, x + radius, y, radius);
  ctx.closePath();
}

export function fillRoundedRect(
  ctx: Ctx,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    ctx.fill();
    return;
  }
  beginRoundedRect(ctx, x, y, w, h, r);
  ctx.fill();
}

export function strokeRoundedRect(
  ctx: Ctx,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    ctx.stroke();
    return;
  }
  beginRoundedRect(ctx, x, y, w, h, r);
  ctx.stroke();
}

// ── Cloud ─────────────────────────────────────────────────────────────────────
export function drawCloud(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const r = 20 * Math.max(0.3, scale);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba("#90A4AE", 0.16);
  [
    [0, 4, r * 0.98],
    [r * 0.95, r * 0.2, r * 0.74],
    [r * 1.9, 4, r * 0.84],
    [-r * 0.82, 4, r * 0.62],
  ].forEach(([dx, dy, rr]) => {
    ctx.beginPath();
    ctx.arc(cx + dx, cy + dy, rr, 0, TAU);
    ctx.fill();
  });
  const grad = ctx.createLinearGradient(cx, cy - r, cx, cy + r * 1.2);
  grad.addColorStop(0, "#FFFFFF");
  grad.addColorStop(1, "#E8F1F9");
  ctx.fillStyle = grad;
  [
    [0, 0, r],
    [r * 0.95, -r * 0.3, r * 0.82],
    [r * 1.9, 0, r * 0.9],
    [-r * 0.82, -r * 0.2, r * 0.72],
  ].forEach(([dx, dy, rr]) => {
    ctx.beginPath();
    ctx.arc(cx + dx, cy + dy, rr, 0, TAU);
    ctx.fill();
  });
  ctx.strokeStyle = rgba("#94A3B8", 0.26);
  ctx.lineWidth = Math.max(1, r * 0.06);
  ctx.beginPath();
  ctx.arc(cx + r * 0.55, cy + r * 0.04, r * 1.75, Math.PI * 0.12, Math.PI * 0.9);
  ctx.stroke();
  ctx.restore();
}

// ── Sun (star version used in solar/heat scenes) ───────────────────────────────
export function drawSol(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  t: number,
  alpha = 1,
) {
  const r = Math.max(8, radius);
  ctx.save();
  ctx.globalAlpha = alpha;

  const halo = ctx.createRadialGradient(cx, cy, r * 0.5, cx, cy, r * 2.3);
  halo.addColorStop(0, rgba("#FDE047", 0.45));
  halo.addColorStop(1, rgba("#FDE047", 0));
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.arc(cx, cy, r * 2.2, 0, TAU);
  ctx.fill();

  for (let i = 0; i < 12; i += 1) {
    const ang = (i / 12) * TAU + t * 0.7;
    const rayLen = r * 0.42 + Math.sin(t * 2 + i) * r * 0.08;
    ctx.strokeStyle = rgba(C.ray, 0.9);
    ctx.lineWidth = Math.max(2, r * 0.08);
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(
      cx + Math.cos(ang) * (r + 2),
      cy + Math.sin(ang) * (r + 2),
    );
    ctx.lineTo(
      cx + Math.cos(ang) * (r + rayLen),
      cy + Math.sin(ang) * (r + rayLen),
    );
    ctx.stroke();
  }

  const grad = ctx.createRadialGradient(
    cx - r * 0.25,
    cy - r * 0.25,
    1,
    cx,
    cy,
    r,
  );
  grad.addColorStop(0, "#FFF9C4");
  grad.addColorStop(0.5, C.sunCore);
  grad.addColorStop(1, C.sunEdge);
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();

  ctx.strokeStyle = rgba("#B45309", 0.4);
  ctx.lineWidth = Math.max(1.2, r * 0.08);
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.95, 0, TAU);
  ctx.stroke();
  ctx.restore();
}

// ── Plant (sunny-face plant character) ────────────────────────────────────────
export function drawSunny(
  ctx: Ctx,
  cx: number,
  groundY: number,
  t: number,
  glowing = false,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.25, scale);
  const sway = Math.sin(t * 1.1) * 4;

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(cx, groundY);
  ctx.scale(s, s);

  ctx.fillStyle = rgba("#14532D", 0.16);
  ctx.beginPath();
  ctx.ellipse(0, 3, 34, 10, 0, 0, TAU);
  ctx.fill();

  ctx.strokeStyle = C.plantStem;
  ctx.lineWidth = 10;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.bezierCurveTo(sway, -38, sway * 0.8, -84, sway * 1.35, -132);
  ctx.stroke();

  const drawLeaf = (
    tx: number,
    ty: number,
    rotation: number,
    flip = false,
    length = 50,
    width = 24,
  ) => {
    ctx.save();
    ctx.translate(tx, ty);
    ctx.rotate(rotation);
    if (flip) ctx.scale(-1, 1);
    ctx.fillStyle = C.leafMain;
    ctx.beginPath();
    ctx.moveTo(-length, 0);
    ctx.bezierCurveTo(-length * 0.45, -width, 0, -width * 0.5, 0, 0);
    ctx.bezierCurveTo(0, width * 0.5, -length * 0.45, width, -length, 0);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = C.leafDark;
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(-length, 0);
    ctx.lineTo(-6, 0);
    ctx.stroke();
    ctx.restore();
  };

  drawLeaf(sway * 0.45 - 10, -78, -0.6);
  drawLeaf(sway * 0.85 + 10, -98, 0.62, true);

  const faceX = sway * 1.2;
  const faceY = -144;
  if (glowing) {
    ctx.save();
    ctx.globalAlpha = 0.15 + Math.sin(t * 3.2) * 0.05;
    ctx.fillStyle = rgba(C.leafMain, 0.6);
    ctx.beginPath();
    ctx.arc(faceX, faceY, 56, 0, TAU);
    ctx.fill();
    ctx.restore();
  }

  const faceGrad = ctx.createRadialGradient(faceX - 8, faceY - 8, 2, faceX, faceY, 24);
  faceGrad.addColorStop(0, "#DFF8E3");
  faceGrad.addColorStop(1, "#9ED8A5");
  ctx.fillStyle = faceGrad;
  ctx.beginPath();
  ctx.arc(faceX, faceY, 22, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = C.leafDark;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "#1B5E20";
  ctx.beginPath();
  ctx.arc(faceX - 6, faceY - 4, 2.8, 0, TAU);
  ctx.arc(faceX + 6, faceY - 4, 2.8, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = "#1B5E20";
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.arc(faceX, faceY + 2, 6, 0.2, Math.PI - 0.2);
  ctx.stroke();
  ctx.restore();
}

// ── Water drop ────────────────────────────────────────────────────────────────
export function drawWaterDrop(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
  color = C.water,
) {
  const r = Math.max(2, radius);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createLinearGradient(cx, cy - r * 1.4, cx, cy + r);
  grad.addColorStop(0, rgba("#D5F4FF", 0.95));
  grad.addColorStop(0.45, color);
  grad.addColorStop(1, C.waterDark);
  ctx.fillStyle = grad;
  ctx.strokeStyle = C.waterDark;
  ctx.lineWidth = Math.max(1.4, r * 0.1);
  ctx.beginPath();
  ctx.moveTo(cx, cy - r * 1.45);
  ctx.bezierCurveTo(cx + r, cy - r * 0.3, cx + r, cy + r * 0.7, cx, cy + r);
  ctx.bezierCurveTo(cx - r, cy + r * 0.7, cx - r, cy - r * 0.3, cx, cy - r * 1.45);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = rgba(C.white, 0.45);
  ctx.beginPath();
  ctx.ellipse(cx - r * 0.3, cy - r * 0.5, r * 0.22, r * 0.34, -0.5, 0, TAU);
  ctx.fill();
  ctx.restore();
}

// ── CO2 molecule ──────────────────────────────────────────────────────────────
export function drawCO2(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
) {
  const r = Math.max(4, radius);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createRadialGradient(cx - r * 0.2, cy - r * 0.2, 1, cx, cy, r);
  grad.addColorStop(0, "#F2F6F8");
  grad.addColorStop(1, C.co2Fill);
  ctx.fillStyle = grad;
  ctx.strokeStyle = C.co2Stroke;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#3A4D56";
  ctx.font = `700 ${Math.max(9, r * 0.58)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("CO₂", cx, cy);
  ctx.restore();
}

// ── O2 molecule ───────────────────────────────────────────────────────────────
export function drawO2(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
) {
  const r = Math.max(4, radius);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createRadialGradient(cx - r * 0.2, cy - r * 0.2, 1, cx, cy, r);
  grad.addColorStop(0, "#F1FFF4");
  grad.addColorStop(1, C.oxygenFill);
  ctx.fillStyle = grad;
  ctx.strokeStyle = C.oxygenStroke;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = C.oxygenStroke;
  ctx.font = `700 ${Math.max(8, r * 0.72)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("O₂", cx, cy);
  ctx.restore();
}

// ── Glucose (hexagon) ─────────────────────────────────────────────────────────
export function drawGlucose(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
  t = 0,
  color = C.glucose,
) {
  const r = Math.max(6, radius);
  const p = pulse(t, 1.8, 0.06, 1);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(cx, cy);
  ctx.scale(p, p);

  ctx.fillStyle = color;
  ctx.strokeStyle = C.glucoseStroke;
  ctx.lineWidth = Math.max(1.8, r * 0.12);
  ctx.beginPath();
  for (let i = 0; i < 6; i += 1) {
    const ang = (i / 6) * TAU - Math.PI / 6;
    const px = Math.cos(ang) * r;
    const py = Math.sin(ang) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.strokeStyle = rgba(C.glucoseStroke, 0.35);
  ctx.lineWidth = Math.max(1, r * 0.06);
  for (let i = 0; i < 6; i += 1) {
    const ang = (i / 6) * TAU - Math.PI / 6;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(Math.cos(ang) * r * 0.72, Math.sin(ang) * r * 0.72);
    ctx.stroke();
  }

  ctx.fillStyle = rgba(C.white, 0.75);
  ctx.font = `bold ${Math.max(7, r * 0.34)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("C₆H₁₂O₆", 0, 0);
  ctx.restore();
}

// ── Bolt / Lightning ──────────────────────────────────────────────────────────
export function drawBolt(
  ctx: Ctx,
  cx: number,
  cy: number,
  size: number,
  alpha = 1,
  color = C.bolt,
) {
  const s = Math.max(4, size);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(cx + s * 0.25, cy - s);
  ctx.lineTo(cx - s * 0.3, cy + s * 0.08);
  ctx.lineTo(cx + s * 0.08, cy + s * 0.08);
  ctx.lineTo(cx - s * 0.25, cy + s);
  ctx.lineTo(cx + s * 0.36, cy - s * 0.04);
  ctx.lineTo(cx - s * 0.04, cy - s * 0.04);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// ── Arrow ─────────────────────────────────────────────────────────────────────
export function drawArrow(
  ctx: Ctx,
  x: number,
  y: number,
  angle: number,
  length: number,
  color = C.arrow,
  thickness = 3,
  alpha = 1,
) {
  if (length <= 0 || alpha <= 0) return;
  const endX = x + Math.cos(angle) * length;
  const endY = y + Math.sin(angle) * length;
  const head = Math.max(8, thickness * 3.6);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createLinearGradient(x, y, endX, endY);
  grad.addColorStop(0, rgba(color, 0.55));
  grad.addColorStop(1, rgba(color, 1));
  ctx.strokeStyle = grad;
  ctx.lineWidth = Math.max(1.4, thickness);
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(
    endX - Math.cos(angle - 0.42) * head,
    endY - Math.sin(angle - 0.42) * head,
  );
  ctx.lineTo(endX, endY);
  ctx.lineTo(
    endX - Math.cos(angle + 0.42) * head,
    endY - Math.sin(angle + 0.42) * head,
  );
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// ── Light ray (dotted) ────────────────────────────────────────────────────────
export function drawLightRay(
  ctx: Ctx,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  alpha = 1,
  color = C.ray,
) {
  if (alpha <= 0) return;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.sqrt(dx * dx + dy * dy);
  const count = Math.max(1, Math.floor(length / 14));
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  for (let i = 0; i <= count; i += 1) {
    const f = i / count;
    ctx.beginPath();
    ctx.arc(lerp(x1, x2, f), lerp(y1, y2, f), 2.2, 0, TAU);
    ctx.fill();
  }
  ctx.restore();
}

// ── Rock ──────────────────────────────────────────────────────────────────────
export function drawRock(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
  color = C.rock,
) {
  const r = Math.max(6, radius);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createLinearGradient(cx - r, cy - r, cx + r, cy + r);
  grad.addColorStop(0, rgba("#D7CCC8", 0.7));
  grad.addColorStop(1, color);
  ctx.fillStyle = grad;
  ctx.strokeStyle = C.rockDark;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - r, cy + r * 0.3);
  ctx.lineTo(cx - r * 0.55, cy - r);
  ctx.lineTo(cx + r * 0.34, cy - r * 0.82);
  ctx.lineTo(cx + r, cy + r * 0.05);
  ctx.lineTo(cx + r * 0.56, cy + r);
  ctx.lineTo(cx - r * 0.5, cy + r);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

// ── Planet ────────────────────────────────────────────────────────────────────
export function drawPlanet(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  alpha = 1,
  color = "#42A5F5",
) {
  const r = Math.max(8, radius);
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createRadialGradient(
    cx - r * 0.3,
    cy - r * 0.3,
    1,
    cx,
    cy,
    r,
  );
  grad.addColorStop(0, "#9ED4FF");
  grad.addColorStop(0.7, color);
  grad.addColorStop(1, "#1565C0");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = rgba("#0F4FA3", 0.45);
  ctx.lineWidth = Math.max(1.4, r * 0.08);
  ctx.stroke();

  ctx.fillStyle = rgba("#66BB6A", 0.45);
  ctx.beginPath();
  ctx.ellipse(cx - r * 0.22, cy - r * 0.12, r * 0.35, r * 0.23, 0.2, 0, TAU);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(cx + r * 0.26, cy + r * 0.15, r * 0.22, r * 0.14, -0.3, 0, TAU);
  ctx.fill();
  ctx.restore();
}

// ── Thermometer ───────────────────────────────────────────────────────────────
export function drawThermometer(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
  fillLevel = 0.5,
) {
  const s = Math.max(0.3, scale);
  const tubeHeight = 100 * s;
  const tubeWidth = 16 * s;
  const bulbR = 18 * s;
  const level = Math.max(0, Math.min(1, fillLevel));

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#F8FAFC";
  fillRoundedRect(ctx, cx - tubeWidth * 0.5, cy - tubeHeight, tubeWidth, tubeHeight, tubeWidth * 0.5);
  ctx.strokeStyle = "#94A3B8";
  ctx.lineWidth = 2;
  strokeRoundedRect(ctx, cx - tubeWidth * 0.5, cy - tubeHeight, tubeWidth, tubeHeight, tubeWidth * 0.5);

  ctx.fillStyle = "#EF4444";
  const fillH = (tubeHeight - 10 * s) * level;
  fillRoundedRect(
    ctx,
    cx - tubeWidth * 0.25,
    cy - 5 * s - fillH,
    tubeWidth * 0.5,
    fillH,
    tubeWidth * 0.25,
  );
  ctx.beginPath();
  ctx.arc(cx, cy + bulbR * 0.1, bulbR, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = "#B91C1C";
  ctx.stroke();
  ctx.restore();
}

// ── Battery ───────────────────────────────────────────────────────────────────
export function drawBattery(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.35, scale);
  const w = 64 * s;
  const h = 34 * s;
  const r = 8 * s;
  const x = cx - w * 0.5;
  const y = cy - h * 0.5;

  ctx.save();
  ctx.globalAlpha = alpha;
  const body = ctx.createLinearGradient(x, y, x, y + h);
  body.addColorStop(0, "#64748B");
  body.addColorStop(1, "#334155");
  ctx.fillStyle = body;
  fillRoundedRect(ctx, x, y, w, h, r);
  ctx.strokeStyle = rgba("#0F172A", 0.4);
  ctx.lineWidth = 1.5;
  strokeRoundedRect(ctx, x, y, w, h, r);

  ctx.fillStyle = C.circuitAccent;
  fillRoundedRect(ctx, x + w * 0.1, y + h * 0.2, w * 0.56, h * 0.6, 4 * s);

  ctx.fillStyle = "#E2E8F0";
  ctx.fillRect(x + w + 2 * s, y + h * 0.32, 6 * s, h * 0.36);
  ctx.fillStyle = "#F8FAFC";
  ctx.font = `700 ${Math.max(8, 11 * s)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("+", x + w * 0.78, y + h * 0.36);
  ctx.fillText("−", x + w * 0.78, y + h * 0.67);
  ctx.restore();
}

/**
 * drawBatterySymbol — schematic battery (two parallel lines, + / −)
 * Used by older domain files that prefer a schematic style.
 */
export function drawBatterySymbol(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  ctx.save();
  ctx.globalAlpha = alpha;

  // body
  const body = ctx.createLinearGradient(cx - 32 * s, cy, cx + 32 * s, cy);
  body.addColorStop(0, "#475569");
  body.addColorStop(1, "#1E293B");
  ctx.fillStyle = body;
  fillRoundedRect(ctx, cx - 32 * s, cy - 16 * s, 64 * s, 32 * s, 6 * s);

  ctx.strokeStyle = rgba(C.circuitAccent, 0.7);
  ctx.lineWidth = 2 * s;
  strokeRoundedRect(ctx, cx - 32 * s, cy - 16 * s, 64 * s, 32 * s, 6 * s);

  // + and − lines
  ctx.strokeStyle = "#FACC15";
  ctx.lineWidth = 3.5 * s;
  ctx.lineCap = "round";
  // long line (−)
  ctx.beginPath();
  ctx.moveTo(cx + 8 * s, cy - 10 * s);
  ctx.lineTo(cx + 8 * s, cy + 10 * s);
  ctx.stroke();
  // short line (+)
  ctx.lineWidth = 5 * s;
  ctx.beginPath();
  ctx.moveTo(cx - 8 * s, cy - 6 * s);
  ctx.lineTo(cx - 8 * s, cy + 6 * s);
  ctx.stroke();

  ctx.fillStyle = "#F8FAFC";
  ctx.font = `700 ${Math.max(7, 10 * s)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("+", cx - 22 * s, cy);
  ctx.fillStyle = "#94A3B8";
  ctx.fillText("−", cx + 22 * s, cy);

  // terminal nub
  ctx.fillStyle = "#64748B";
  ctx.fillRect(cx + 32 * s, cy - 4 * s, 6 * s, 8 * s);

  ctx.restore();
}

// ── Switch ────────────────────────────────────────────────────────────────────
export function drawSwitch(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
  closed = true,
) {
  const s = Math.max(0.35, scale);
  const w = 52 * s;
  const h = 22 * s;
  const x = cx - w * 0.5;
  const y = cy - h * 0.5;

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba("#E2E8F0", 0.75);
  fillRoundedRect(ctx, x, y, w, h, h * 0.5);
  ctx.strokeStyle = rgba("#334155", 0.45);
  ctx.lineWidth = 1.4;
  strokeRoundedRect(ctx, x, y, w, h, h * 0.5);

  const knobR = h * 0.38;
  const kx = closed ? x + w * 0.68 : x + w * 0.3;
  ctx.fillStyle = closed ? C.circuitAccent : "#94A3B8";
  ctx.beginPath();
  ctx.arc(kx, cy, knobR, 0, TAU);
  ctx.fill();
  ctx.restore();
}

// ── Wire loop / circuit outline ────────────────────────────────────────────────
export function drawWireLoop(
  ctx: Ctx,
  x: number,
  y: number,
  w: number,
  h: number,
  alpha = 1,
  color = "#FACC15",
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, 18);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.moveTo(x + 18, y);
    ctx.lineTo(x + w - 18, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + 18);
    ctx.lineTo(x + w, y + h - 18);
    ctx.quadraticCurveTo(x + w, y + h, x + w - 18, y + h);
    ctx.lineTo(x + 18, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - 18);
    ctx.lineTo(x, y + 18);
    ctx.quadraticCurveTo(x, y, x + 18, y);
    ctx.stroke();
  }
  ctx.restore();
}

/**
 * drawCircuitLoop — draws a complete circuit rectangle with battery, switch and bulb,
 * used by domain files as an anchor.
 */
export function drawCircuitLoop(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const w = 200 * s;
  const h = 110 * s;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = "#FACC15";
  ctx.lineWidth = 3 * s;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  // draw rectangle (the wire loop)
  ctx.beginPath();
  ctx.rect(cx - w * 0.5, cy - h * 0.5, w, h);
  ctx.stroke();
  ctx.restore();
}

/**
 * drawGlowingBulb — a lit light bulb (brighter than drawBulb actor).
 */
export function drawGlowingBulb(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const r = 18 * s;

  ctx.save();
  ctx.globalAlpha = alpha;

  // glow halo
  const glow = ctx.createRadialGradient(cx, cy, r * 0.3, cx, cy, r * 2.4);
  glow.addColorStop(0, rgba("#FDE047", 0.55));
  glow.addColorStop(1, rgba("#FDE047", 0));
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(cx, cy, r * 2.4, 0, TAU);
  ctx.fill();

  // bulb glass
  const bulbGrad = ctx.createRadialGradient(cx - r * 0.25, cy - r * 0.25, 1, cx, cy, r);
  bulbGrad.addColorStop(0, "#FFFDE7");
  bulbGrad.addColorStop(0.6, "#FDE047");
  bulbGrad.addColorStop(1, "#F59E0B");
  ctx.fillStyle = bulbGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = rgba("#92400E", 0.5);
  ctx.lineWidth = 1.5 * s;
  ctx.stroke();

  // base/socket
  ctx.fillStyle = "#64748B";
  ctx.fillRect(cx - r * 0.42, cy + r * 0.72, r * 0.84, r * 0.7);
  strokeRoundedRect(ctx, cx - r * 0.42, cy + r * 0.72, r * 0.84, r * 0.7, 2 * s);

  ctx.restore();
}

/**
 * drawBulbDark — an unlit light bulb.
 */
export function drawBulbDark(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const r = 18 * s;

  ctx.save();
  ctx.globalAlpha = alpha;

  ctx.fillStyle = rgba("#94A3B8", 0.22);
  ctx.beginPath();
  ctx.arc(cx, cy, r * 1.6, 0, TAU);
  ctx.fill();

  const bulbGrad = ctx.createRadialGradient(cx - r * 0.2, cy - r * 0.2, 1, cx, cy, r);
  bulbGrad.addColorStop(0, "#E2E8F0");
  bulbGrad.addColorStop(1, "#94A3B8");
  ctx.fillStyle = bulbGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, TAU);
  ctx.fill();
  ctx.strokeStyle = rgba("#475569", 0.5);
  ctx.lineWidth = 1.5 * s;
  ctx.stroke();

  ctx.fillStyle = "#475569";
  ctx.fillRect(cx - r * 0.42, cy + r * 0.72, r * 0.84, r * 0.7);

  ctx.restore();
}

/**
 * drawWirePath — draws a rectangular wire outline, alias for drawCircuitLoop
 * with slightly different defaults for domain files.
 */
export function drawWirePath(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const w = 180 * s;
  const h = 100 * s;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = "#FACC15";
  ctx.lineWidth = 2.5 * s;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.rect(cx - w * 0.5, cy - h * 0.5, w, h);
  ctx.stroke();
  ctx.restore();
}

/**
 * drawCurrentArrow — animated current flow arrow for circuit scenes.
 */
export function drawCurrentArrow(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const len = 60 * s;
  drawArrow(ctx, cx - len * 0.5, cy, 0, len, "#FACC15", 3 * s, alpha);
}

// ── Volcano ───────────────────────────────────────────────────────────────────
export function drawVolcano(
  ctx: Ctx,
  cx: number,
  cy: number,
  size = 60,
  alpha = 1,
) {
  const s = Math.max(16, size);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#6D4C41";
  ctx.beginPath();
  ctx.moveTo(cx - s, cy + s * 0.24);
  ctx.lineTo(cx - s * 0.44, cy - s);
  ctx.lineTo(cx + s * 0.44, cy - s);
  ctx.lineTo(cx + s, cy + s * 0.24);
  ctx.lineTo(cx + s * 0.76, cy + s * 0.54);
  ctx.lineTo(cx - s * 0.76, cy + s * 0.54);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = rgba("#FF6D00", 0.92);
  ctx.beginPath();
  ctx.ellipse(cx, cy - s, s * 0.3, s * 0.15, 0, 0, TAU);
  ctx.fill();
  ctx.restore();
}

// ── Wave arc (sound) ──────────────────────────────────────────────────────────
export function drawWaveArc(
  ctx: Ctx,
  cx: number,
  cy: number,
  radius: number,
  phase = 0,
  alpha = 1,
  color = C.arrow,
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, -0.7 + phase, 0.7 + phase);
  ctx.stroke();
  ctx.restore();
}

// ── Concept pill ──────────────────────────────────────────────────────────────
export function drawConceptPill(
  ctx: Ctx,
  cx: number,
  cy: number,
  alpha = 1,
  color = C.arrow,
  text = "Concept",
) {
  const w = Math.max(80, text.length * 8 + 28);
  const h = 34;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba(C.white, 0.95);
  fillRoundedRect(ctx, cx - w * 0.5, cy - h * 0.5, w, h, h * 0.5);
  ctx.strokeStyle = rgba(color, 0.4);
  ctx.lineWidth = 1.5;
  strokeRoundedRect(ctx, cx - w * 0.5, cy - h * 0.5, w, h, h * 0.5);
  ctx.fillStyle = color;
  ctx.font = "600 13px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, cx, cy);
  ctx.restore();
}

// ── Education card ────────────────────────────────────────────────────────────
export function drawEducationCard(
  ctx: Ctx,
  W: number,
  H: number,
  text: string,
  alpha = 1,
  _t = 0,
  conceptTitle = "",
  accent = C.arrow,
) {
  const cardW = Math.min(W * 0.82, 540);
  const cardH = Math.min(H * 0.34, 220);
  const x = (W - cardW) * 0.5;
  const y = H * 0.08;

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba(C.white, 0.96);
  fillRoundedRect(ctx, x, y, cardW, cardH, 16);
  ctx.strokeStyle = rgba(accent, 0.3);
  ctx.lineWidth = 1.5;
  strokeRoundedRect(ctx, x, y, cardW, cardH, 16);
  ctx.fillStyle = accent;
  ctx.fillRect(x, y, cardW, 5);

  if (conceptTitle) {
    ctx.fillStyle = rgba(accent, 0.12);
    fillRoundedRect(ctx, x + 14, y + 14, Math.min(cardW - 28, conceptTitle.length * 8 + 28), 24, 12);
    ctx.fillStyle = accent;
    ctx.font = "700 12px sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(conceptTitle, x + 24, y + 26);
  }

  ctx.fillStyle = C.cardText;
  ctx.font = "600 17px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  const maxWidth = cardW - 36;
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width <= maxWidth) {
      line = next;
      continue;
    }
    if (line) lines.push(line);
    line = word;
    if (lines.length >= 3) break;
  }
  if (line && lines.length < 4) lines.push(line);

  const startY = y + cardH * 0.52 - ((lines.length - 1) * 24) * 0.5;
  lines.forEach((ln, index) => {
    const clipped =
      ctx.measureText(ln).width > maxWidth
        ? `${ln.slice(0, Math.max(8, ln.length - 3))}...`
        : ln;
    ctx.fillText(clipped, x + cardW * 0.5, startY + index * 24);
  });
  ctx.restore();
}

// ── Additional Color Aliases ───────────────────────────────────────────────────
// Added so domain files that reference these won't blow up even if we add them
// to C later. For now they map to existing values.
Object.assign(C, {
  indoorWall: "rgba(240,248,255,0.18)",  // used in respiration.ts drawBackground
} as any);

// ── Sound wave arcs (used by sensitivity_response) ────────────────────────────
export function drawSoundWaveArcs(
  ctx: Ctx,
  cx: number,
  cy: number,
  t: number,
  alpha = 1,
) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  [1, 2, 3].forEach((i) => {
    const a = alpha * (1 - i * 0.22);
    const r = i * 14 + Math.sin(t * 3) * 2;
    ctx.strokeStyle = `rgba(37,99,235,${a})`;
    ctx.lineWidth = 2.5 - i * 0.5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, -0.7, 0.7);
    ctx.stroke();
  });
  ctx.restore();
}

// ── Lungs diagram (used by respiration) ───────────────────────────────────────
export function drawLungs(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
  breatheScale = 1,
) {
  const s = Math.max(0.3, scale);
  const b = Math.max(0.7, breatheScale);
  ctx.save();
  ctx.globalAlpha = alpha;

  // Left lung
  ctx.fillStyle = rgba("#F48FB1", 0.3);
  ctx.strokeStyle = "#F48FB1";
  ctx.lineWidth = 2 * s;
  ctx.beginPath();
  ctx.ellipse(cx - 28 * s * b, cy, 22 * s * b, 38 * s * b, 0.12, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Right lung
  ctx.beginPath();
  ctx.ellipse(cx + 28 * s * b, cy, 22 * s * b, 38 * s * b, -0.12, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Trachea
  ctx.strokeStyle = "#E91E63";
  ctx.lineWidth = 3 * s;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(cx, cy - 38 * s * b);
  ctx.lineTo(cx, cy - 58 * s);
  ctx.stroke();
  // Bronchi
  ctx.beginPath();
  ctx.moveTo(cx, cy - 38 * s * b);
  ctx.lineTo(cx - 26 * s * b, cy - 22 * s * b);
  ctx.moveTo(cx, cy - 38 * s * b);
  ctx.lineTo(cx + 26 * s * b, cy - 22 * s * b);
  ctx.stroke();

  ctx.restore();
}

// ── Chest breathing arc ────────────────────────────────────────────────────────
export function drawChestArc(
  ctx: Ctx,
  cx: number,
  cy: number,
  r: number,
  alpha = 1,
) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = rgba("#E91E63", 0.5);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, Math.max(8, r), Math.PI * 0.15, Math.PI * 0.85);
  ctx.stroke();
  ctx.restore();
}

// ── States of matter shapes ────────────────────────────────────────────────────

export function drawSolidContainer(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const w = 52 * s;
  const h = 44 * s;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = rgba("#90A4AE", 0.16);
  ctx.strokeStyle = "#607D8B";
  ctx.lineWidth = 2 * s;
  ctx.fillRect(cx - w * 0.5, cy - h * 0.5, w, h);
  ctx.strokeRect(cx - w * 0.5, cy - h * 0.5, w, h);
  ctx.restore();
}

export function drawLiquidBeaker(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const w = 44 * s;
  const h = 56 * s;
  const y = cy - h * 0.5;
  ctx.save();
  ctx.globalAlpha = alpha;

  // beaker outline
  ctx.strokeStyle = "#90A4AE";
  ctx.lineWidth = 2 * s;
  ctx.beginPath();
  ctx.moveTo(cx - w * 0.5, y);
  ctx.lineTo(cx - w * 0.55, y + h);
  ctx.lineTo(cx + w * 0.55, y + h);
  ctx.lineTo(cx + w * 0.5, y);
  ctx.stroke();

  // liquid fill
  ctx.fillStyle = rgba("#29B6F6", 0.5);
  ctx.beginPath();
  ctx.moveTo(cx - w * 0.52, y + h * 0.38);
  ctx.lineTo(cx - w * 0.55, y + h);
  ctx.lineTo(cx + w * 0.55, y + h);
  ctx.lineTo(cx + w * 0.52, y + h * 0.38);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function drawGasBalloon(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
) {
  const s = Math.max(0.3, scale);
  const r = 26 * s;
  ctx.save();
  ctx.globalAlpha = alpha;

  // balloon
  ctx.fillStyle = rgba("#CE93D8", 0.4);
  ctx.strokeStyle = "#9C27B0";
  ctx.lineWidth = 2 * s;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // string
  ctx.strokeStyle = "#7B1FA2";
  ctx.lineWidth = 1.5 * s;
  ctx.beginPath();
  ctx.moveTo(cx, cy + r);
  ctx.bezierCurveTo(cx + 4 * s, cy + r + 10 * s, cx - 4 * s, cy + r + 20 * s, cx, cy + r + 28 * s);
  ctx.stroke();

  // gas symbol
  ctx.fillStyle = "#6A1B9A";
  ctx.font = `bold ${Math.max(9, 11 * s)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("G", cx, cy);

  ctx.restore();
}

export function drawParticleDots(
  ctx: Ctx,
  cx: number,
  cy: number,
  stateType: "solid" | "liquid" | "gas",
  alpha = 1,
) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha * 0.72;

  const configs: Record<string, { r: number; spacing: number; jitter: number; color: string }> = {
    solid: { r: 4, spacing: 10, jitter: 0, color: "#607D8B" },
    liquid: { r: 4, spacing: 12, jitter: 3, color: "#29B6F6" },
    gas: { r: 3, spacing: 18, jitter: 8, color: "#9C27B0" },
  };
  const { r, spacing, jitter, color } = configs[stateType] || configs.solid;

  ctx.fillStyle = color;
  for (let row = -2; row <= 2; row++) {
    for (let col = -2; col <= 2; col++) {
      const px = cx + col * spacing + (Math.random() * jitter - jitter * 0.5);
      const py = cy + row * spacing + (Math.random() * jitter - jitter * 0.5);
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.restore();
}

// ── Magnet shape ──────────────────────────────────────────────────────────────
export function drawMagnet(
  ctx: Ctx,
  cx: number,
  cy: number,
  scale = 1,
  alpha = 1,
  orientation: "horizontal" | "vertical" = "horizontal",
) {
  const s = Math.max(0.3, scale);
  ctx.save();
  ctx.globalAlpha = alpha;

  if (orientation === "horizontal") {
    const w = 60 * s;
    const h = 20 * s;
    // North (red)
    ctx.fillStyle = "#EF5350";
    ctx.fillRect(cx - w, cy - h * 0.5, w, h);
    // South (blue)
    ctx.fillStyle = "#42A5F5";
    ctx.fillRect(cx, cy - h * 0.5, w, h);

    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 1 * s;
    ctx.strokeRect(cx - w, cy - h * 0.5, w * 2, h);

    // Labels
    ctx.fillStyle = "#FFFFFF";
    ctx.font = `bold ${Math.max(8, 11 * s)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("N", cx - w * 0.5, cy);
    ctx.fillText("S", cx + w * 0.5, cy);
  } else {
    // Vertical U-magnet
    const lw = 14 * s;
    const lh = 40 * s;
    const gap = 24 * s;
    // Left arm (N)
    ctx.fillStyle = "#EF5350";
    ctx.fillRect(cx - gap * 0.5 - lw, cy - lh * 0.5, lw, lh);
    // Right arm (S)
    ctx.fillStyle = "#42A5F5";
    ctx.fillRect(cx + gap * 0.5, cy - lh * 0.5, lw, lh);
    // Bridge
    ctx.fillStyle = "#78909C";
    ctx.fillRect(cx - gap * 0.5 - lw, cy - lh * 0.5, gap + lw * 2, lw);

    ctx.fillStyle = "#FFFFFF";
    ctx.font = `bold ${Math.max(8, 10 * s)}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("N", cx - gap * 0.5 - lw * 0.5, cy + lh * 0.18);
    ctx.fillText("S", cx + gap * 0.5 + lw * 0.5, cy + lh * 0.18);
  }

  ctx.restore();
}

