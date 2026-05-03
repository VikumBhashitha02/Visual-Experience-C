/**
 * animation/sceneRenderers.ts
 * Step-by-step educational renderer with domain-aware visual sequencing.
 */

import { layoutActorsForScene, renderLaidOutActors } from "./actorRenderers";
import {
  DOMAIN_VISUALS,
  detectDomain as detectDomainFromCore,
  type ConceptDomain,
} from "./core/domainDetector";
import { clamp, clamp01, easeOutCubic, fadeIn, lerp, smoothstep } from "./core/easing";
import {
  C,
  drawArrow,
  drawBattery,
  drawBolt,
  drawCO2,
  drawCloud,
  drawConceptPill,
  drawGlowingBulb,
  drawGlucose,
  drawLightRay,
  drawLungs,
  drawMagnet,
  drawO2,
  drawPlanet,
  drawRock,
  drawSol,
  drawSunny,
  drawSwitch,
  drawThermometer,
  drawWaterDrop,
  drawWaveArc,
  drawWireLoop,
} from "./core/shapes";

type Ctx = any;
type CognitiveMode = "OVERLOAD" | "OPTIMAL" | "LOW_LOAD";

export type { ConceptDomain };

export interface StepDef {
  label: string;
  weight?: number;
  persist?: number;
  render: (
    ctx: Ctx,
    progress: number,
    t: number,
    W: number,
    H: number,
    strength: number,
  ) => void;
  focus?: (W: number, H: number) => { x: number; y: number; r: number };
}

type StepWindow = { index: number; start: number; duration: number };

/** Actor types emitted by the Python rule engine — always drawable (domain whitelist is bypassed). */
const RULE_ENGINE_ACTOR_TYPES = new Set([
  "sun", "star", "cloud", "ocean", "mountain", "molecule", "plant", "leaf", "root", "rock", "volcano",
  "co2", "oxygen", "glucose", "water", "waterdrop", "bolt", "wave", "thermometer", "arrow", "line",
  "planet", "moon", "earth", "asteroid", "comet", "cell", "bacteria", "animal", "atom", "electron",
  "proton", "neutron", "battery", "wire", "switch", "bulb", "ear", "label", "thermometer",
]);

function syllabusTopicToClientDomain(topic: string): ConceptDomain | null {
  const t = (topic || "").toLowerCase().trim();
  if (t === "water_cycle") return "water_cycle";
  if (t === "plant_processes") return "photosynthesis";
  if (t === "energy" || t === "solar_energy") return "heat_transfer";
  if (t === "wind_energy") return "generic";
  return null;
}

const DOMAIN_ALLOWED_TYPES: Partial<Record<ConceptDomain, Set<string>>> = {
  photosynthesis: new Set([
    "sun", "plant", "leaf", "root", "waterdrop", "water",
    "co2", "oxygen", "glucose", "arrow", "label", "line", "bolt", "cloud",
  ]),
  water_cycle: new Set([
    "sun", "cloud", "ocean", "mountain", "molecule", "waterdrop", "water", "arrow", "label", "line", "rock",
    "thermometer",
  ]),
  food_chain: new Set([
    "plant", "animal", "arrow", "label", "line",
    "bird", "rabbit", "deer", "lion", "fox", "snake",
  ]),
  electric_circuit: new Set([
    "battery", "wire", "switch", "bulb", "arrow", "label", "line", "bolt", "wave",
  ]),
  sound: new Set(["wave", "ear", "arrow", "label", "line", "bolt"]),
  heat_transfer: new Set(["sun", "rock", "arrow", "label", "line", "bolt", "thermometer", "wave"]),
  gravity: new Set(["planet", "rock", "arrow", "label", "line"]),
  solar_system: new Set(["sun", "planet", "rock", "arrow", "label", "line"]),
  respiration: new Set(["oxygen", "co2", "arrow", "label", "line", "molecule", "animal"]),
  human_body: new Set(["label", "arrow", "line", "molecule", "oxygen", "co2", "animal", "ear"]),
};

const TYPE_ALIAS: Record<string, string> = {
  water_drop: "waterdrop",
  droplet: "waterdrop",
  h2o: "waterdrop",
  carbon_dioxide: "co2",
  carbondioxide: "co2",
  molecule_co2: "co2",
  o2: "oxygen",
  molecule_o2: "oxygen",
  sugar: "glucose",
  glucose_molecule: "glucose",
  energy: "bolt",
  lightning: "bolt",
  star: "sun",
  tree: "plant",
  stem: "plant",
  leaves: "leaf",
  roots: "root",
  earth: "planet",
  globe: "planet",
  battery_cell: "battery",
  lamp: "bulb",
  conductor: "wire",
  circuit: "wire",
  sound_wave: "wave",
  vibration: "wave",
  cell: "molecule",
};

function semanticHint(text: string): string | null {
  const lower = text.toLowerCase();
  if (hasToken(lower, "battery")) return "battery";
  if (hasToken(lower, "wire", "wires")) return "wire";
  if (hasToken(lower, "switch")) return "switch";
  if (hasToken(lower, "bulb", "lamp", "light bulb")) return "bulb";
  if (hasToken(lower, "current")) return "arrow";
  if (hasToken(lower, "co2", "carbon dioxide")) return "co2";
  if (hasToken(lower, "oxygen", "o2")) return "oxygen";
  if (hasToken(lower, "water", "h2o")) return "waterdrop";
  if (hasToken(lower, "glucose", "sugar")) return "glucose";
  if (hasToken(lower, "leaf")) return "leaf";
  if (hasToken(lower, "root")) return "root";
  return null;
}

function canonicalActorType(actor: any): string {
  const raw = String(actor?.type || "label").toLowerCase().trim();
  const mapped = TYPE_ALIAS[raw] || raw;
  const hint = semanticHint(String(actor?.text || ""));
  if (hint && (mapped === "label" || mapped === "shape" || mapped === "object" || mapped === "star")) {
    return hint;
  }
  return mapped;
}

function sanitizeActorsForDomain(
  domain: ConceptDomain,
  actors: any[],
  text: string,
  scene?: any,
): any[] {
  if (!Array.isArray(actors)) return [];
  if (scene?.meta?.pipeline === "rule_engine") {
    return actors
      .filter(Boolean)
      .map((actor) => ({ ...actor, type: canonicalActorType(actor) }))
      .filter((actor) => RULE_ENGINE_ACTOR_TYPES.has(String(actor.type || "").toLowerCase()));
  }
  const allowed = DOMAIN_ALLOWED_TYPES[domain];
  const sceneHint = semanticHint(text);
  const out: any[] = [];

  for (const actor of actors) {
    const type = canonicalActorType(actor);
    const hinted = semanticHint(String(actor?.text || ""));
    const finalType = hinted || (sceneHint && (type === "star" || type === "sun") ? sceneHint : type);
    const fromEngine = RULE_ENGINE_ACTOR_TYPES.has(finalType);
    const isAllowed =
      fromEngine ||
      !allowed ||
      allowed.has(finalType) ||
      finalType === "label" ||
      finalType === "arrow" ||
      finalType === "line";
    if (!isAllowed) continue;

    // Prevent cross-domain leaks explicitly in strict domains.
    if (domain === "electric_circuit" && ["sun", "plant", "leaf", "root", "glucose", "co2", "oxygen", "waterdrop", "water", "cloud"].includes(finalType)) {
      continue;
    }

    out.push({ ...actor, type: finalType });
  }

  return out;
}

function ensureDomainEssentials(domain: ConceptDomain, actors: any[], text: string): any[] {
  if (domain !== "electric_circuit") return actors;
  const out = Array.isArray(actors) ? [...actors] : [];
  const present = new Set(out.map((actor) => canonicalActorType(actor)));
  const fallback = inferActorsFromText(domain, text);
  const essential: string[] = ["battery", "wire", "switch", "bulb"];

  essential.forEach((type) => {
    if (present.has(type)) return;
    const candidate = fallback.find((actor) => canonicalActorType(actor) === type);
    if (candidate) {
      out.push(candidate);
      present.add(type);
    }
  });

  if (hasToken(text.toLowerCase(), "label", "labels", "parts")) {
    const hasLabel = out.some((actor) => canonicalActorType(actor) === "label");
    if (!hasLabel) {
      out.push(
        { type: "label", text: "Battery", x: 0.2, y: 0.62, fontSize: 13, color: "#F8FAFC" },
        { type: "label", text: "Switch", x: 0.58, y: 0.24, fontSize: 13, color: "#F8FAFC" },
        { type: "label", text: "Bulb", x: 0.84, y: 0.24, fontSize: 13, color: "#F8FAFC" },
        { type: "label", text: "Wires", x: 0.46, y: 0.22, fontSize: 13, color: "#F8FAFC" },
      );
    }
  }

  return out;
}

function resolveSceneDomain(baseDomain: ConceptDomain, scene: any, text: string): ConceptDomain {
  const sceneCandidate = detectDomainFromCore(text || "", [scene]);
  if (sceneCandidate !== "generic" && sceneCandidate !== baseDomain) return sceneCandidate;
  if (baseDomain === "generic" && sceneCandidate !== "generic") return sceneCandidate;
  return baseDomain;
}

export function detectDomain(title: string, scenes: any[]): ConceptDomain {
  return detectDomainFromCore(title, scenes);
}

function isLabelOnly(actors: any[]): boolean {
  if (!Array.isArray(actors) || actors.length === 0) return true;
  return actors.every((actor) => !actor || String(actor.type || "label").toLowerCase() === "label");
}

function hasToken(text: string, ...tokens: string[]): boolean {
  const lower = text.toLowerCase();
  return tokens.some((token) => lower.includes(token));
}

/**
 * Teaching tier from pipeline cognitive_load (low | medium | high).
 * Drives speed, density, and visual complexity — distinct from a transient student state.
 */
function resolveCognitiveMode(scene: any): CognitiveMode {
  const load = String(scene?.meta?.cognitive_load ?? "").toLowerCase().trim();
  if (load === "low") return "LOW_LOAD";
  if (load === "high") return "OVERLOAD";

  const legacy = String(
    scene?.meta?.cognitiveState ?? scene?.meta?.cognitive_state ?? scene?.meta?.state ?? "",
  )
    .toUpperCase()
    .trim();
  if (legacy === "OVERLOAD") return "OVERLOAD";
  if (legacy === "LOW" || legacy === "LOW_LOAD" || legacy === "LOWLOAD") return "LOW_LOAD";
  return "OPTIMAL";
}

function simplifyActorsForOverload(actors: any[]): any[] {
  if (!Array.isArray(actors) || actors.length <= 5) return actors || [];
  const importance: Record<string, number> = {
    sun: 9,
    star: 9,
    plant: 10,
    root: 8,
    leaf: 8,
    glucose: 8,
    co2: 7,
    oxygen: 7,
    water: 7,
    waterdrop: 7,
    battery: 10,
    wire: 8,
    switch: 8,
    bulb: 9,
    arrow: 6,
    label: 3,
  };
  return [...actors]
    .sort((a, b) => {
      const ta = String(a?.type || "").toLowerCase();
      const tb = String(b?.type || "").toLowerCase();
      const sa = importance[ta] ?? 4;
      const sb = importance[tb] ?? 4;
      return sb - sa;
    })
    .slice(0, 5);
}

function drawDomainBackground(
  ctx: Ctx,
  domain: ConceptDomain,
  W: number,
  H: number,
  t: number,
  cognitiveMode?: CognitiveMode,
) {
  const theme = DOMAIN_VISUALS[domain] ?? DOMAIN_VISUALS.generic;
  const sky = ctx.createLinearGradient(0, 0, 0, H * 0.72);
  sky.addColorStop(0, theme.backgroundTop);
  sky.addColorStop(1, theme.backgroundBottom);
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, H);

  if (cognitiveMode === "LOW_LOAD") {
    ctx.save();
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.fillRect(0, 0, W, H * 0.45);
    ctx.restore();
  } else if (cognitiveMode === "OVERLOAD") {
    ctx.save();
    ctx.fillStyle = "rgba(15,23,42,0.14)";
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    const g = (t * 14) % 48;
    for (let x = -48; x <= W + 48; x += 48) {
      ctx.beginPath();
      ctx.moveTo(x + g, 0);
      ctx.lineTo(x + g, H);
      ctx.stroke();
    }
    ctx.restore();
  }

  if (theme.ground) {
    const soil = ctx.createLinearGradient(0, H * 0.68, 0, H);
    soil.addColorStop(0, theme.ground);
    soil.addColorStop(1, "#4E342E");
    ctx.fillStyle = soil;
    ctx.fillRect(0, H * 0.68, W, H * 0.32);
    ctx.fillStyle = C.grass;
    ctx.fillRect(0, H * 0.68, W, 18);
  }

  if (domain === "electric_circuit") {
    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.lineWidth = 1;
    const offset = (t * 18) % 40;
    for (let x = -40; x <= W + 40; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x + offset, 0);
      ctx.lineTo(x + offset, H);
      ctx.stroke();
    }
    for (let y = -40; y <= H + 40; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y + offset);
      ctx.lineTo(W, y + offset);
      ctx.stroke();
    }
    ctx.restore();
    return;
  }

  if (domain !== "solar_system") {
    drawCloud(ctx, W * 0.14 + Math.sin(t * 0.25) * 20, H * 0.1, 1, 0.82);
    drawCloud(ctx, W * 0.68 + Math.cos(t * 0.22) * 18, H * 0.12, 0.85, 0.74);
  }
}

function drawPersistentAnchors(
  domain: ConceptDomain,
  ctx: Ctx,
  W: number,
  H: number,
  t: number,
  alpha: number,
) {
  if (alpha <= 0.01) return;
  if (domain === "photosynthesis") {
    drawSunny(ctx, W * 0.24, H * 0.79, t, true, 0.98, alpha);
    drawSol(ctx, W * 0.82, H * 0.14, 48, t, alpha * 0.92);
    return;
  }
  if (domain === "water_cycle") {
    drawSol(ctx, W * 0.8, H * 0.16, 40, t, alpha * 0.9);
    drawCloud(ctx, W * 0.52, H * 0.18, 1.1, alpha * 0.78);
    return;
  }
  if (domain === "electric_circuit") {
    drawBattery(ctx, W * 0.2, H * 0.5, 1, alpha * 0.95);
    drawWireLoop(ctx, W * 0.16, H * 0.32, W * 0.68, H * 0.32, alpha * 0.62, "#FACC15");
    drawSwitch(ctx, W * 0.57, H * 0.32, 0.8, alpha * 0.86, true);
    return;
  }
  if (domain === "heat_transfer") {
    drawSol(ctx, W * 0.24, H * 0.5, 36, t, alpha);
    drawRock(ctx, W * 0.78, H * 0.54, 34, alpha * 0.88, "#9CA3AF");
    drawThermometer(ctx, W * 0.84, H * 0.42, 0.7, alpha * 0.6, 0.6);
    return;
  }
  if (domain === "gravity") {
    drawPlanet(ctx, W * 0.5, H * 0.78, 86, alpha * 0.86);
    return;
  }
  if (domain === "solar_system") {
    drawSol(ctx, W * 0.18, H * 0.5, 40, t, alpha * 0.9);
    return;
  }
  if (domain === "respiration") {
    const breathe = 0.95 + Math.sin(t * 0.9) * 0.07;
    drawLungs(ctx, W * 0.5, H * 0.52, 1.1, alpha * 0.35, breathe);
    return;
  }
  if (domain === "human_body") {
    ctx.save();
    ctx.globalAlpha = alpha * 0.18;
    ctx.strokeStyle = "#EF9A9A";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(W * 0.5, H * 0.46, 80, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
    return;
  }
}

function inferActorsFromText(domain: ConceptDomain, text: string): any[] {
  const lower = text.toLowerCase();
  if (domain === "photosynthesis") {
    return [
      { type: "sun", x: 0.82, y: 0.14, size: 0.1, animation: "rotate" },
      { type: "plant", x: 0.24, y: 0.79, size: 0.24, animation: "sway" },
      { type: "root", x: 0.24, y: 0.86, size: 0.14, animation: "idle" },
      hasToken(lower, "water", "h2o", "root")
        ? { type: "waterdrop", x: 0.16, y: 0.82, size: 0.07, animation: "float" }
        : null,
      hasToken(lower, "co2", "carbon dioxide")
        ? { type: "co2", x: 0.74, y: 0.31, size: 0.075, animation: "drift" }
        : null,
      hasToken(lower, "glucose", "food", "sugar")
        ? { type: "glucose", x: 0.55, y: 0.44, size: 0.085, animation: "pulse" }
        : null,
      hasToken(lower, "oxygen", "o2")
        ? { type: "oxygen", x: 0.66, y: 0.21, size: 0.07, animation: "float" }
        : null,
    ].filter(Boolean);
  }
  if (domain === "water_cycle") {
    return [
      { type: "sun", x: 0.8, y: 0.16, size: 0.1, animation: "rotate" },
      { type: "cloud", x: 0.52, y: 0.19, size: 0.11, animation: "float" },
      { type: "waterdrop", x: 0.3, y: 0.74, size: 0.065, animation: "bounce" },
      { type: "waterdrop", x: 0.44, y: 0.74, size: 0.06, animation: "bounce" },
      { type: "waterdrop", x: 0.58, y: 0.74, size: 0.065, animation: "bounce" },
    ];
  }
  if (domain === "food_chain") {
    return [
      { type: "plant", x: 0.16, y: 0.79, size: 0.22, animation: "sway" },
      { type: "animal", x: 0.48, y: 0.72, size: 0.14, animation: "idle", label: "Herbivore" },
      { type: "animal", x: 0.8, y: 0.7, size: 0.16, animation: "idle", label: "Carnivore" },
      { type: "arrow", x: 0.25, y: 0.68, angle: 0, length: 0.18, color: "#4CAF50" },
      { type: "arrow", x: 0.57, y: 0.67, angle: 0, length: 0.16, color: "#EF6C00" },
    ];
  }
  if (domain === "electric_circuit") {
    const openSwitch = hasToken(lower, "open switch", "incomplete", "does not light", "off");
    const closedSwitch = hasToken(lower, "closed switch", "complete circuit", "current flows", "lights", "on");
    const switchClosed = closedSwitch || !openSwitch;
    return [
      { type: "battery", x: 0.2, y: 0.5, size: 0.13, animation: "pulse" },
      { type: "wire", x: 0.5, y: 0.48, length: 0.62, animation: "idle", color: "#FACC15" },
      { type: "switch", x: 0.58, y: 0.32, size: 0.1, animation: "idle", closed: switchClosed },
      { type: "bulb", x: 0.84, y: 0.32, size: 0.1, animation: switchClosed ? "glow" : "idle" },
    ];
  }
  if (domain === "sound") {
    return [
      { type: "wave", x: 0.28, y: 0.5, size: 0.12, animation: "pulse", color: "#1D4ED8" },
      { type: "arrow", x: 0.42, y: 0.5, angle: 0, length: 0.28, color: "#1D4ED8" },
      { type: "ear", x: 0.82, y: 0.5, size: 0.1, animation: "idle" },
    ];
  }
  if (domain === "heat_transfer") {
    return [
      { type: "sun", x: 0.24, y: 0.5, size: 0.1, animation: "pulse" },
      { type: "arrow", x: 0.34, y: 0.5, angle: 0, length: 0.3, color: "#EA580C" },
      { type: "rock", x: 0.78, y: 0.54, size: 0.1, animation: "idle", color: "#94A3B8" },
    ];
  }
  if (domain === "gravity") {
    return [
      { type: "planet", x: 0.5, y: 0.78, size: 0.22, animation: "pulse" },
      { type: "rock", x: 0.5, y: 0.24, size: 0.08, animation: "fall" },
      { type: "arrow", x: 0.5, y: 0.32, angle: Math.PI / 2, length: 0.28, color: "#1D4ED8" },
    ];
  }
  if (domain === "respiration") {
    return [
      { type: "oxygen", x: 0.2, y: 0.44, size: 0.08, animation: "float" },
      { type: "arrow", x: 0.26, y: 0.46, angle: 0, length: 0.18, color: "#22C55E" },
      { type: "co2", x: 0.78, y: 0.44, size: 0.08, animation: "drift" },
    ];
  }
  return [
    { type: "label", x: 0.5, y: 0.46, text: text || "Science concept" },
    { type: "arrow", x: 0.32, y: 0.56, angle: 0, length: 0.34 },
  ];
}

function getDomainSteps(domain: ConceptDomain, text: string): StepDef[] {
  if (domain === "photosynthesis") {
    const lower = text.toLowerCase();
    const includeWater = hasToken(lower, "water", "root", "h2o");
    const includeCo2 = hasToken(lower, "co2", "carbon dioxide", "air");
    const includeGlucose = hasToken(lower, "glucose", "food", "sugar");
    const includeOxygen = hasToken(lower, "oxygen", "o2", "release");
    return [
      { label: "Step 1: Plant and Sun appear", weight: 1.05, persist: 0.45, render: (ctx, p, t, W, H, s) => { drawSunny(ctx, W * 0.24, H * 0.79, t, true, 0.6 + p * 0.4, p * s); drawSol(ctx, W * 0.82, H * 0.14, 48 * p, t, p * s); }, focus: (W, H) => ({ x: W * 0.54, y: H * 0.46, r: 120 }) },
      { label: "Step 2: Light rays move to the leaf", weight: 1.15, persist: 0.4, render: (ctx, p, _t, W, H, s) => { drawLightRay(ctx, W * 0.76, H * 0.2, W * 0.34, H * 0.5, p * s); drawArrow(ctx, W * 0.7, H * 0.23, Math.PI - 0.55, W * 0.24 * p, "#F59E0B", 3, p * s); }, focus: (W, H) => ({ x: W * 0.48, y: H * 0.38, r: 90 }) },
      ...(includeWater ? [{ label: "Step 3: Water rises from roots", weight: 1.12, persist: 0.35, render: (ctx: Ctx, p: number, _t: number, W: number, H: number, s: number) => { const y = lerp(H * 0.84, H * 0.46, smoothstep(p)); drawWaterDrop(ctx, W * 0.24, y, 12, p * s); drawArrow(ctx, W * 0.24, H * 0.8, -Math.PI / 2, H * 0.28 * p, "#0288D1", 3, p * s); }, focus: (W: number, H: number) => ({ x: W * 0.24, y: H * 0.62, r: 72 }) }] : []),
      ...(includeCo2 ? [{ label: "Step 4: CO2 enters the leaf", weight: 1.08, persist: 0.32, render: (ctx: Ctx, p: number, _t: number, W: number, H: number, s: number) => { const x = lerp(W * 0.76, W * 0.4, smoothstep(p)); drawCO2(ctx, x, H * 0.3, 22, p * s); drawArrow(ctx, W * 0.72, H * 0.3, Math.PI + 0.12, W * 0.28 * p, "#90A4AE", 3, p * s); }, focus: (W: number, H: number) => ({ x: W * 0.45, y: H * 0.35, r: 72 }) }] : []),
      { label: "Step 5: Energy conversion happens", weight: 1.06, persist: 0.3, render: (ctx, p, _t, W, H, s) => { drawBolt(ctx, W * 0.44, H * 0.4, 30 * p, p * s, "#8B5CF6"); }, focus: (W, H) => ({ x: W * 0.44, y: H * 0.4, r: 58 }) },
      ...(includeGlucose ? [{ label: "Step 6: Glucose is produced", weight: 1.1, persist: 0.28, render: (ctx: Ctx, p: number, t: number, W: number, H: number, s: number) => { drawGlucose(ctx, W * 0.56, H * 0.44, 28 * p, p * s, t, "#FB923C"); }, focus: (W: number, H: number) => ({ x: W * 0.56, y: H * 0.44, r: 58 }) }] : []),
      ...(includeOxygen ? [{ label: "Step 7: Oxygen exits the plant", weight: 1.12, persist: 0.24, render: (ctx: Ctx, p: number, _t: number, W: number, H: number, s: number) => { const x = lerp(W * 0.42, W * 0.68, smoothstep(p)); const y = lerp(H * 0.38, H * 0.22, smoothstep(p)); drawO2(ctx, x, y, 17, p * s); drawArrow(ctx, W * 0.4, H * 0.38, -0.45, W * 0.22 * p, "#22C55E", 3, p * s); }, focus: (W: number, H: number) => ({ x: W * 0.58, y: H * 0.26, r: 72 }) }] : []),
    ];
  }
  if (domain === "water_cycle") {
    return [
      { label: "Step 1: Sun heats water", weight: 1.05, persist: 0.42, render: (ctx, p, t, W, H, s) => { drawSol(ctx, W * 0.78, H * 0.16, 44 * p, t, p * s);[0, 1, 2].forEach((i) => drawWaterDrop(ctx, W * (0.28 + i * 0.08), H * 0.76, 12, p * s)); }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.66, r: 108 }) },
      { label: "Step 2: Evaporation rises", weight: 1.12, persist: 0.35, render: (ctx, p, _t, W, H, s) => { drawArrow(ctx, W * 0.44, H * 0.72, -Math.PI / 2, H * 0.28 * p, "#0288D1", 3, p * s); }, focus: (W, H) => ({ x: W * 0.44, y: H * 0.5, r: 82 }) },
      { label: "Step 3: Condensation forms clouds", weight: 1.03, persist: 0.32, render: (ctx, p, _t, W, H, s) => drawCloud(ctx, W * 0.5, H * 0.2, 1.2 * p, p * s), focus: (W, H) => ({ x: W * 0.5, y: H * 0.2, r: 82 }) },
      { label: "Step 4: Rain falls", weight: 1.16, persist: 0.28, render: (ctx, p, _t, W, H, s) => { for (let i = 0; i < 5; i += 1) { const x = W * 0.35 + i * W * 0.07; const y = lerp(H * 0.3, H * 0.72, smoothstep(p)); drawWaterDrop(ctx, x, y, 10, p * s * (1 - i * 0.08)); } }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.5, r: 110 }) },
      { label: "Step 5: Water collects", weight: 1.06, persist: 0.22, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.2, H * 0.86, 0, W * 0.6 * p, "#0288D1", 3, p * s), focus: (W, H) => ({ x: W * 0.52, y: H * 0.8, r: 120 }) },
    ];
  }
  if (domain === "electric_circuit") {
    const lower = text.toLowerCase();
    const openSwitch = hasToken(lower, "open switch", "incomplete", "does not light", "off");
    const closedSwitch = hasToken(lower, "closed switch", "complete circuit", "current flows", "lights", "on");
    const switchClosed = closedSwitch || !openSwitch;
    return [
      { label: "Step 1: Battery provides energy", weight: 1.05, persist: 0.42, render: (ctx, p, _t, W, H, s) => drawBattery(ctx, W * 0.2, H * 0.5, 0.85 + p * 0.15, p * s), focus: (W, H) => ({ x: W * 0.2, y: H * 0.5, r: 62 }) },
      { label: "Step 2: Current starts through wire", weight: 1.16, persist: 0.37, render: (ctx, p, _t, W, H, s) => { drawWireLoop(ctx, W * 0.16, H * 0.32, W * 0.68, H * 0.32, p * s * 0.72, "#FACC15"); drawArrow(ctx, W * 0.28, H * 0.32, 0, W * 0.24 * p, "#FACC15", 4, p * s); }, focus: (W, H) => ({ x: W * 0.44, y: H * 0.32, r: 72 }) },
      { label: switchClosed ? "Step 3: Switch closes" : "Step 3: Switch stays open", weight: 1.08, persist: 0.32, render: (ctx, p, _t, W, H, s) => drawSwitch(ctx, W * 0.57, H * 0.32, 0.9, p * s, switchClosed ? p > 0.45 : false), focus: (W, H) => ({ x: W * 0.57, y: H * 0.32, r: 54 }) },
      { label: switchClosed ? "Step 4: Current reaches bulb" : "Step 4: Current is blocked", weight: 1.02, persist: 0.28, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.7, H * 0.32, 0, (switchClosed ? W * 0.12 : W * 0.04) * p, "#FACC15", 4, p * s), focus: (W, H) => ({ x: W * 0.8, y: H * 0.32, r: 58 }) },
      { label: switchClosed ? "Step 5: Bulb lights up" : "Step 5: Bulb remains off", weight: 1.18, persist: 0.22, render: (ctx, p, t, W, H, s) => { const glow = switchClosed ? 0.2 + Math.max(0, Math.sin(t * 8)) * 0.3 * p : 0.12; ctx.save(); ctx.globalAlpha = p * s; ctx.fillStyle = switchClosed ? `rgba(250,204,21,${glow})` : "rgba(148,163,184,0.16)"; ctx.beginPath(); ctx.arc(W * 0.84, H * 0.32, 34, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }, focus: (W, H) => ({ x: W * 0.84, y: H * 0.32, r: 72 }) },
    ];
  }
  if (domain === "sound") {
    return [
      { label: "Step 1: A source vibrates", weight: 1.08, persist: 0.4, render: (ctx, p, t, W, H, s) => { const vib = Math.sin(t * 20) * 6 * p; ctx.save(); ctx.globalAlpha = p * s; ctx.strokeStyle = "#1D4ED8"; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(W * 0.2, H * 0.42 + vib); ctx.lineTo(W * 0.2, H * 0.58 - vib); ctx.stroke(); ctx.restore(); }, focus: (W, H) => ({ x: W * 0.2, y: H * 0.5, r: 58 }) },
      { label: "Step 2: Sound waves spread", weight: 1.15, persist: 0.34, render: (ctx, p, t, W, H, s) => { [0, 1, 2, 3].forEach((i) => drawWaveArc(ctx, W * 0.24, H * 0.5, (i + 1) * (24 + p * 8), t * 0.4, p * s * (1 - i * 0.15), "#1D4ED8")); }, focus: (W, H) => ({ x: W * 0.44, y: H * 0.5, r: 96 }) },
      { label: "Step 3: Waves travel to the ear", weight: 1.05, persist: 0.3, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.42, H * 0.5, 0, W * 0.28 * p, "#1D4ED8", 3, p * s), focus: (W, H) => ({ x: W * 0.72, y: H * 0.5, r: 72 }) },
      { label: "Step 4: Hearing signal is formed", weight: 1.06, persist: 0.22, render: (ctx, p, _t, W, H, s) => drawBolt(ctx, W * 0.9, H * 0.46, 20 * p, p * s, "#2563EB"), focus: (W, H) => ({ x: W * 0.84, y: H * 0.5, r: 66 }) },
    ];
  }
  if (domain === "heat_transfer") {
    return [
      { label: "Step 1: Heat source starts", weight: 1.1, persist: 0.4, render: (ctx, p, t, W, H, s) => drawSol(ctx, W * 0.24, H * 0.5, 40 * p, t, p * s), focus: (W, H) => ({ x: W * 0.24, y: H * 0.5, r: 66 }) },
      { label: "Step 2: Heat transfers", weight: 1.2, persist: 0.35, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.34, H * 0.5, 0, W * 0.34 * p, "#EA580C", 4, p * s), focus: (W, H) => ({ x: W * 0.54, y: H * 0.5, r: 92 }) },
      { label: "Step 3: Colder object warms up", weight: 1.1, persist: 0.24, render: (ctx, p, _t, W, H, s) => { drawRock(ctx, W * 0.78, H * 0.54, 34, p * s, "#9CA3AF"); drawBolt(ctx, W * 0.78, H * 0.46, 24 * p, p * s, "#EA580C"); }, focus: (W, H) => ({ x: W * 0.78, y: H * 0.52, r: 68 }) },
    ];
  }
  if (domain === "gravity") {
    return [
      { label: "Step 1: Earth pulls objects", weight: 1.08, persist: 0.42, render: (ctx, p, _t, W, H, s) => drawPlanet(ctx, W * 0.5, H * 0.78, 80 * p, p * s), focus: (W, H) => ({ x: W * 0.5, y: H * 0.78, r: 90 }) },
      { label: "Step 2: Pull is downward", weight: 1.2, persist: 0.34, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.5, H * 0.28, Math.PI / 2, H * 0.32 * p, "#1D4ED8", 4, p * s), focus: (W, H) => ({ x: W * 0.5, y: H * 0.46, r: 84 }) },
      { label: "Step 3: Object falls", weight: 1.12, persist: 0.24, render: (ctx, p, _t, W, H, s) => drawRock(ctx, W * 0.5, lerp(H * 0.26, H * 0.62, easeOutCubic(p)), 24, p * s), focus: (W, H) => ({ x: W * 0.5, y: H * 0.52, r: 72 }) },
    ];
  }
  if (domain === "solar_system") {
    return [
      { label: "Step 1: The Sun is the centre", weight: 1.1, persist: 0.42, render: (ctx, p, t, W, H, s) => drawSol(ctx, W * 0.18, H * 0.5, 46 * p, t, p * s), focus: (W, H) => ({ x: W * 0.18, y: H * 0.5, r: 60 }) },
      {
        label: "Step 2: Planets orbit in paths", weight: 1.15, persist: 0.36, render: (ctx, p, _t, W, H, s) => {
          ctx.save(); ctx.globalAlpha = p * s * 0.25; ctx.strokeStyle = "#90A4AE"; ctx.lineWidth = 1;
          [0.2, 0.3, 0.42].forEach((r) => { ctx.beginPath(); ctx.ellipse(W * 0.18, H * 0.5, r * W, r * W * 0.36, 0, 0, Math.PI * 2); ctx.stroke(); });
          ctx.restore();
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.5, r: 160 })
      },
      {
        label: "Step 3: Earth orbits the Sun", weight: 1.12, persist: 0.32, render: (ctx, p, t, W, H, s) => {
          const ang = t * 0.5; const dist = W * 0.3;
          drawPlanet(ctx, W * 0.18 + Math.cos(ang) * dist, H * 0.5 + Math.sin(ang) * dist * 0.36, 18 * p, p * s, "#42A5F5");
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.5, r: 140 })
      },
      { label: "Step 4: Gravity holds the system", weight: 1.05, persist: 0.22, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.42, H * 0.5, Math.PI, W * 0.2 * p, "#60A5FA", 3, p * s), focus: (W, H) => ({ x: W * 0.3, y: H * 0.5, r: 80 }) },
    ];
  }
  if (domain === "respiration") {
    const lower = text.toLowerCase();
    const isInhale = hasToken(lower, "inhal", "oxygen", "breathe in");
    const isExhale = hasToken(lower, "exhal", "carbon dioxide", "breathe out");
    return [
      {
        label: "Step 1: Lungs expand on inhale", weight: 1.1, persist: 0.42, render: (ctx, p, t, W, H, s) => {
          const breathe = 0.9 + p * 0.12 + Math.sin(t * 1.8) * 0.04;
          drawLungs(ctx, W * 0.5, H * 0.52, 1.2, p * s, breathe);
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.52, r: 80 })
      },
      {
        label: isExhale ? "Step 2: CO2 is breathed out" : "Step 2: O2 enters the blood", weight: 1.15, persist: 0.35, render: (ctx, p, _t, W, H, s) => {
          if (isExhale) {
            const x = lerp(W * 0.6, W * 0.84, smoothstep(p));
            drawCO2(ctx, x, H * 0.42, 20, p * s);
            drawArrow(ctx, W * 0.6, H * 0.42, 0, W * 0.22 * p, "#EF9A9A", 3, p * s);
          } else {
            const x = lerp(W * 0.2, W * 0.4, smoothstep(p));
            drawO2(ctx, x, H * 0.42, 20, p * s);
            drawArrow(ctx, W * 0.2, H * 0.42, 0, W * 0.2 * p, "#22C55E", 3, p * s);
          }
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.44, r: 110 })
      },
      {
        label: "Step 3: Gas exchange complete", weight: 1.06, persist: 0.24, render: (ctx, p, _t, W, H, s) => {
          drawO2(ctx, W * 0.22, H * 0.44, 16, p * s * 0.8);
          drawArrow(ctx, W * 0.28, H * 0.44, 0, W * 0.14 * p, "#22C55E", 2, p * s * 0.8);
          drawCO2(ctx, W * 0.78, H * 0.44, 16, p * s * 0.8);
          drawArrow(ctx, W * 0.62, H * 0.44, 0, W * 0.1 * p, "#EF9A9A", 2, p * s * 0.8);
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.48, r: 130 })
      },
    ];
  }
  if (domain === "human_body") {
    return [
      {
        label: "Step 1: Body systems work together", weight: 1.05, persist: 0.42, render: (ctx, p, t, W, H, s) => {
          ctx.save(); ctx.globalAlpha = p * s * 0.4; ctx.strokeStyle = "#EF9A9A"; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(W * 0.5, H * 0.44, 88 * p, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
          drawBolt(ctx, W * 0.5, H * 0.28, 22 * p, p * s * 0.7, "#E91E63");
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.46, r: 100 })
      },
      {
        label: "Step 2: Blood carries oxygen", weight: 1.15, persist: 0.35, render: (ctx, p, _t, W, H, s) => {
          drawO2(ctx, W * 0.24, H * 0.44, 18, p * s);
          drawArrow(ctx, W * 0.32, H * 0.46, 0, W * 0.36 * p, "#E91E63", 3, p * s);
          drawArrow(ctx, W * 0.78, H * 0.46, Math.PI, W * 0.18 * p, "#EF5350", 3, p * s * 0.7);
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.46, r: 110 })
      },
      {
        label: "Step 3: Energy for body functions", weight: 1.08, persist: 0.24, render: (ctx, p, _t, W, H, s) => {
          drawBolt(ctx, W * 0.34, H * 0.38, 20 * p, p * s, "#E91E63");
          drawBolt(ctx, W * 0.5, H * 0.52, 18 * p, p * s * 0.8, "#E91E63");
          drawBolt(ctx, W * 0.66, H * 0.38, 16 * p, p * s * 0.7, "#E91E63");
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.46, r: 100 })
      },
    ];
  }
  if (domain === "food_chain") {
    return [
      { label: "Step 1: Producers make food", weight: 1.1, persist: 0.42, render: (ctx, p, t, W, H, s) => drawSunny(ctx, W * 0.16, H * 0.79, t, false, 0.85 * p, p * s), focus: (W, H) => ({ x: W * 0.16, y: H * 0.6, r: 72 }) },
      {
        label: "Step 2: Herbivore eats plants", weight: 1.12, persist: 0.36, render: (ctx, p, _t, W, H, s) => {
          drawArrow(ctx, W * 0.22, H * 0.67, 0, W * 0.18 * p, "#4CAF50", 4, p * s);
          ctx.save(); ctx.globalAlpha = p * s;
          ctx.fillStyle = "#D4A373"; ctx.fillRect(W * 0.42, H * 0.62, 36 * p, 22 * p);
          ctx.restore();
        }, focus: (W, H) => ({ x: W * 0.34, y: H * 0.67, r: 80 })
      },
      {
        label: "Step 3: Carnivore eats herbivore", weight: 1.12, persist: 0.32, render: (ctx, p, _t, W, H, s) => {
          drawArrow(ctx, W * 0.52, H * 0.66, 0, W * 0.2 * p, "#EF6C00", 4, p * s);
          ctx.save(); ctx.globalAlpha = p * s;
          ctx.fillStyle = "#EF5350"; ctx.fillRect(W * 0.74, H * 0.6, 40 * p, 24 * p);
          ctx.restore();
        }, focus: (W, H) => ({ x: W * 0.66, y: H * 0.66, r: 90 })
      },
      {
        label: "Step 4: Energy flows along chain", weight: 1.06, persist: 0.22, render: (ctx, p, _t, W, H, s) => {
          drawBolt(ctx, W * 0.5, H * 0.48, 22 * p, p * s, "#F59E0B");
          drawArrow(ctx, W * 0.16, H * 0.56, 0, W * 0.7 * p, "#F59E0B", 2, p * s * 0.5);
        }, focus: (W, H) => ({ x: W * 0.5, y: H * 0.56, r: 200 })
      },
    ];
  }

  return [
    { label: "Key idea", weight: 1.1, persist: 0.34, render: (ctx, p, _t, W, H, s) => { drawConceptPill(ctx, W * 0.5, H * 0.46, p * s, "#2563EB", "Key idea"); drawBolt(ctx, W * 0.5, H * 0.58, 16 * p, p * s, "#2563EB"); } },
    { label: "Observe and explain", weight: 1, persist: 0.2, render: (ctx, p, _t, W, H, s) => drawArrow(ctx, W * 0.32, H * 0.56, 0, W * 0.36 * p, "#2563EB", 3, p * s) },
  ];
}

function computeStepWindows(steps: StepDef[], durationMs: number, mode: CognitiveMode): StepWindow[] {
  if (!steps.length) return [];
  const speedFactor = mode === "OVERLOAD" ? 0.8 : mode === "LOW_LOAD" ? 1.2 : 1;
  const intro = Math.min(500, durationMs * (mode === "OVERLOAD" ? 0.14 : mode === "LOW_LOAD" ? 0.06 : 0.08));
  const outro = Math.min(500, durationMs * (mode === "OVERLOAD" ? 0.12 : mode === "LOW_LOAD" ? 0.05 : 0.06));
  const usable = Math.max(steps.length * 560, durationMs - intro - outro);
  const weights = steps.map((step) => Math.max(0.55, step.weight ?? 1));
  const totalWeight = weights.reduce((sum, value) => sum + value, 0) || 1;
  const windows: StepWindow[] = [];
  let cursor = intro;
  for (let i = 0; i < steps.length; i += 1) {
    const rawDuration = i === steps.length - 1 ? durationMs - outro - cursor : (usable * weights[i]) / totalWeight;
    const duration = rawDuration * speedFactor;
    windows.push({ index: i, start: cursor, duration: Math.max(1, duration) });
    cursor += duration;
  }
  return windows;
}

function drawFocusRing(ctx: Ctx, x: number, y: number, r: number, alpha: number, t: number) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = "rgba(255,255,255,0.94)";
  ctx.lineWidth = 2;
  ctx.setLineDash?.([7, 6]);
  ctx.beginPath();
  ctx.arc(x, y, r * (1 + Math.sin(t * 4.2) * 0.04), 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash?.([]);
  ctx.restore();
}

function renderStepSequence(
  steps: StepDef[],
  elapsedMs: number,
  sceneDurationMs: number,
  t: number,
  W: number,
  H: number,
  ctx: Ctx,
  strength: number,
  mode: CognitiveMode,
): string {
  if (!steps.length) return "";
  const windows = computeStepWindows(steps, sceneDurationMs, mode);
  const e = clamp(elapsedMs, 0, sceneDurationMs);
  let active = windows[windows.length - 1];
  for (const window of windows) {
    if (e >= window.start && e <= window.start + window.duration) {
      active = window;
      break;
    }
  }
  const local = clamp01((e - active.start) / (active.duration * 0.86));
  const eased = easeOutCubic(local);
  const activeIdx = active.index;

  for (let i = 0; i < activeIdx; i += 1) {
    const age = activeIdx - i;
    const linger = clamp(steps[i].persist ?? 0.34, 0.12, 0.62);
    const ghostFactor = mode === "OVERLOAD" ? 0.48 : 1;
    const ghost = strength * linger * ghostFactor * Math.max(0.2, 1 - age * 0.2);
    steps[i].render(ctx, 1, t, W, H, ghost);
  }

  steps[activeIdx].render(ctx, eased, t, W, H, strength);
  if (mode !== "OVERLOAD" && local > 0.82 && activeIdx < steps.length - 1) {
    const preCue = smoothstep((local - 0.82) / 0.18);
    steps[activeIdx + 1].render(ctx, preCue * 0.3, t, W, H, strength * 0.22);
  }

  const focus = steps[activeIdx].focus?.(W, H);
  if (focus) drawFocusRing(ctx, focus.x, focus.y, focus.r, 0.22 + eased * 0.66 * strength, t);
  return steps[activeIdx].label;
}

function renderCaption(
  ctx: Ctx,
  sceneText: string,
  stepLabel: string,
  elapsedMs: number,
  W: number,
  H: number,
) {
  const display = stepLabel || sceneText;
  if (!display) return;
  const alpha = fadeIn(elapsedMs, 90, 420);
  if (alpha < 0.01) return;
  const barH = 48;
  const barY = H - barH - 10;
  const barX = W * 0.04;
  const barW = W * 0.92;
  ctx.save();
  ctx.globalAlpha = alpha;
  const grad = ctx.createLinearGradient(0, barY, 0, barY + barH);
  grad.addColorStop(0, "rgba(15,23,42,0.6)");
  grad.addColorStop(1, "rgba(2,6,23,0.9)");
  ctx.fillStyle = grad;
  if (typeof ctx.roundRect === "function") {
    ctx.beginPath();
    ctx.roundRect(barX, barY, barW, barH, 12);
    ctx.fill();
  } else {
    ctx.fillRect(barX, barY, barW, barH);
  }
  if (stepLabel) {
    ctx.fillStyle = "#60A5FA";
    ctx.beginPath();
    ctx.arc(barX + 18, barY + barH * 0.5, 4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = "#FFFFFF";
  ctx.font = "600 14px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const maxW = barW - 36;
  let out = display;
  while (ctx.measureText(out).width > maxW && out.length > 12) {
    out = `${out.slice(0, -4)}...`;
  }
  ctx.fillText(out, barX + barW * 0.5, barY + barH * 0.5);
  ctx.restore();
}

/** Quadratic Bézier point: P0→P1 control→P2 end (Canvas quadraticCurveTo convention). */
function quadPoint(
  p0: { x: number; y: number },
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  u: number,
) {
  const s = 1 - u;
  return {
    x: s * s * p0.x + 2 * s * u * p1.x + u * u * p2.x,
    y: s * s * p0.y + 2 * s * u * p1.y + u * u * p2.y,
  };
}

// ─── Backend animation link renderer ─────────────────────────────────────────
// Curved flow paths + direction cues (Grade 6 clarity over decoration).
function renderBackendAnimations(
  animations: any[],
  actorMap: Map<string, { x: number; y: number }>,
  ctx: Ctx,
  elapsedMs: number,
  alpha: number,
  W: number,
  H: number,
  scene?: any,
) {
  if (!Array.isArray(animations) || animations.length === 0) return;
  const flowStart = Number(scene?.meta?.flow_start_ms ?? 0);
  const flowGate = flowStart > 0 ? clamp01((elapsedMs - flowStart) / 560) : 1;
  const flowColors: Record<string, string> = {
    emit: "#FFD700",
    flow: "#2196F3",
    absorb: "#4CAF50",
    transform: "#9C27B0",
    orbit: "#90A4AE",
    attract: "#F44336",
    repel: "#FF9800",
    evaporation: "#FFB74D",
    condensation: "#B3E5FC",
    precipitation: "#64B5F6",
    photosynthesis: "#81C784",
    respiration: "#A5D6A7",
    energy_transfer: "#FFD54F",
    fall: "#42A5F5",
    rise: "#4FC3F7",
    rotate: "#CE93D8",
  };

  for (const anim of animations) {
    const from = actorMap.get(anim.from);
    const to = actorMap.get(anim.to);
    if (!from || !to) continue;

    const color = flowColors[anim.type] || "#90A4AE";
    const dir = String(anim.direction || "along").toLowerCase();
    const mx = (from.x + to.x) * 0.5;
    const my = (from.y + to.y) * 0.5;
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    let cx = mx;
    let cy = my;
    if (dir === "up") cy = my - H * 0.11;
    else if (dir === "down") cy = my + H * 0.11;
    else if (dir === "transform") {
      cx = mx + W * 0.05;
      cy = my - H * 0.06;
    } else {
      cx = mx + (dy / len) * 42;
      cy = my - (dx / len) * 42;
    }

    const p0 = from;
    const p1 = { x: cx, y: cy };
    const p2 = to;

    const angle = Math.atan2(to.y - from.y, to.x - from.x);

    const offset = (elapsedMs * 0.032) % 22;
    ctx.save();
    ctx.globalAlpha = alpha * flowGate * 0.74;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3.2;
    ctx.lineCap = "round";
    ctx.setLineDash?.([10, 9]);
    ctx.lineDashOffset = -offset;
    ctx.beginPath();
    ctx.moveTo(p0.x, p0.y);
    ctx.quadraticCurveTo(p1.x, p1.y, p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash?.([]);

    // Moving packet — phase loops smoothly on curve (no jump at wrap).
    const dur = typeof anim.duration === "number" && anim.duration > 2600 ? anim.duration : 3800;
    const u = dur > 0 ? (((elapsedMs % dur) + dur) % dur) / dur : 0;
    const pkt = quadPoint(p0, p1, p2, (u * 0.88 + 0.06) % 1);
    ctx.globalAlpha = alpha * flowGate * 0.95;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(pkt.x, pkt.y, 5.2, 0, Math.PI * 2);
    ctx.fill();

    const headLen = 12;
    ctx.globalAlpha = alpha * flowGate * 0.9;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.8;
    ctx.beginPath();
    ctx.moveTo(to.x, to.y);
    ctx.lineTo(
      to.x - headLen * Math.cos(angle - 0.44),
      to.y - headLen * Math.sin(angle - 0.44),
    );
    ctx.moveTo(to.x, to.y);
    ctx.lineTo(
      to.x - headLen * Math.cos(angle + 0.44),
      to.y - headLen * Math.sin(angle + 0.44),
    );
    ctx.stroke();
    ctx.restore();
  }
}

export function renderUniversalScene(
  scene: any,
  domain: ConceptDomain,
  ctx: Ctx,
  W: number,
  H: number,
  elapsedMs: number,
  sceneBlend = 1,
  visualElapsedMs?: number,
): void {
  ctx.save();
  ctx.globalAlpha = (typeof ctx.globalAlpha === "number" ? ctx.globalAlpha : 1) * clamp01(sceneBlend);

  const ve = visualElapsedMs ?? elapsedMs;
  const t = ve * 0.001;
  const text = String(scene?.text || scene?.focus || "");
  const duration = typeof scene?.duration === "number" && scene.duration > 0 ? scene.duration : 6000;
  const segmentDuration =
    typeof scene?.meta?.loop_segment_ms === "number" && scene.meta.loop_segment_ms > 0
      ? scene.meta.loop_segment_ms
      : duration;
  const cognitiveMode = resolveCognitiveMode(scene);
  const forcedDomain = syllabusTopicToClientDomain(String(scene?.meta?.syllabus_topic || ""));
  const sceneDomain = forcedDomain || resolveSceneDomain(domain, scene, text);

  drawDomainBackground(ctx, sceneDomain, W, H, t, cognitiveMode);

  // ── Determine actors to render ────────────────────────────────────────────
  // Priority: backend actors > inferred fallback
  const rawActors = Array.isArray(scene?.actors) ? scene.actors : [];
  const sanitizedActors = sanitizeActorsForDomain(sceneDomain, rawActors, text, scene);
  const hasBackendActors = sanitizedActors.length > 0 && !isLabelOnly(sanitizedActors);

  const inferredActors = inferActorsFromText(sceneDomain, text);
  const baseActors = ensureDomainEssentials(
    sceneDomain,
    hasBackendActors ? sanitizedActors : inferredActors,
    text,
  );
  const activeActors = simplifyActorsForOverload(baseActors);

  // Persistent anchors — LOW keeps distraction minimal; OVERLOAD tier adds faint structure.
  const anchorAlpha = hasBackendActors
    ? cognitiveMode === "OVERLOAD"
      ? 0.22
      : cognitiveMode === "LOW_LOAD"
        ? 0.11
        : 0.14
    : isLabelOnly(sanitizedActors)
      ? 0.9
      : cognitiveMode === "OVERLOAD"
        ? 0.44
        : cognitiveMode === "LOW_LOAD"
          ? 0.24
          : 0.28;
  drawPersistentAnchors(sceneDomain, ctx, W, H, t, anchorAlpha);

  // Inject timeline if not present
  const actorsWithTimeline = activeActors.map((actor: any, index: number) => {
    const hasTimeline = Array.isArray(actor?.timeline) && actor.timeline.length > 0;
    if (hasTimeline) return actor;
    const start = Math.min(index * 200, 1200);
    return {
      ...actor,
      timeline: [
        { at: start, alpha: 0 },
        { at: start + 580, alpha: 1, easing: "easeOut" as const },
      ],
    };
  });

  // Single layout pass: flow lines must use the same x/y as sprite drawing (autoLayoutActors).
  const laidOut = layoutActorsForScene(actorsWithTimeline, W, H);

  // ── Render backend animations[] (flow lines between actors) ──────────────
  if (hasBackendActors && Array.isArray(scene?.animations) && scene.animations.length > 0) {
    const actorMap = new Map<string, { x: number; y: number }>();
    for (const actor of laidOut) {
      const rawId = actor.id != null && actor.id !== "" ? String(actor.id) : "";
      if (!rawId) continue;
      actorMap.set(rawId, { x: actor.x, y: actor.y });
    }
    const linkMul =
      cognitiveMode === "OVERLOAD" ? 0.52 : cognitiveMode === "LOW_LOAD" ? 0.92 : 0.78;
    const linkAlpha = Math.min(1, ve / 900) * linkMul;
    renderBackendAnimations(scene.animations, actorMap, ctx, ve, linkAlpha, W, H, scene);
  }

  const focusActorId =
    String(scene?.meta?.focus_actor_id || "").trim() ||
    (laidOut.find((a: any) => String(a?.role || "").toLowerCase() === "cause")?.id as string | undefined) ||
    (laidOut[0]?.id as string | undefined);

  const lc = Math.max(1, Number(scene?.meta?.loop_count ?? 1));
  const segMs =
    typeof scene?.meta?.loop_segment_ms === "number" && scene.meta.loop_segment_ms > 0
      ? scene.meta.loop_segment_ms
      : 0;
  const loopIdx = segMs > 0 ? Math.min(lc - 1, Math.floor(elapsedMs / segMs)) : 0;

  const actorCount = renderLaidOutActors(laidOut, ctx, ve, W, H, {
    focusActorId: focusActorId || null,
    visualElapsedMs: ve,
    loopSegmentMs: Number(scene?.meta?.loop_segment_ms ?? 0),
    segmentTailPauseMs: Number(scene?.meta?.segment_tail_pause_ms ?? 0),
    loopIndex: loopIdx,
  });

  // ── Domain step overlay (reduced when backend actors are present) ─────────
  const steps = getDomainSteps(sceneDomain, text);
  // When backend drives the scene, domain steps are only a faint ambient layer
  const overlayStrength = hasBackendActors
    ? 0                                     // backend actors = no hardcoded step overlay
    : isLabelOnly(sanitizedActors)
      ? 1
      : cognitiveMode === "OVERLOAD"
        ? 0.88
        : cognitiveMode === "LOW_LOAD"
          ? 0.58
          : 0.66;

  const stepLabel = overlayStrength > 0
    ? renderStepSequence(steps, ve, segmentDuration, t, W, H, ctx, overlayStrength, cognitiveMode)
    : "";

  if (actorCount === 0 && steps.length === 0) {
    drawConceptPill(ctx, W * 0.5, H * 0.5, 0.9, "#2563EB", "Learning step");
  }

  // Use focus field (v2) in preference to scene text for the caption
  const captionText = String(scene?.focus || text)
    .trim()
    .split(/\s+/)
    .slice(0, 5)
    .join(" ");
  renderCaption(ctx, captionText, stepLabel, ve, W, H);
  ctx.endFrameEXP?.();
  ctx.restore();
}
