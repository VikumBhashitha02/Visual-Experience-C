/**
 * animation/scriptNormalizer.ts
 * Sanitizes backend animation scripts for renderer safety.
 */

export interface AnimationLink {
  type: string;
  from: string;
  to: string;
  duration?: number;
  /** Backend hint: up | down | along | transform — curved flow rendering */
  direction?: string;
}

/**
 * A single timed event inside a scene's sequence.
 * Events are sorted by `time` (ms offset from scene startTime).
 */
export interface SequenceEvent {
  time: number;           // ms offset from scene startTime
  action: string;         // appear | move | glow | pulse | emit | flow | absorb | transform | hide
  target: string;         // actor id
  to?: { x?: number; y?: number; [key: string]: any }; // destination for 'move'
  to_target?: string;     // second actor id for emit/flow/absorb
  value?: any;            // optional extra param
}

export interface RawActor {
  id?: string;
  type?: string;
  role?: string;
  x?: number | null;
  y?: number | null;
  animation?: string;
  color?: string | null;
  size?: number | null;
  count?: number | null;
  angle?: number | null;
  length?: number | null;
  thickness?: number | null;
  text?: string;
  fontSize?: number | null;
  rays?: boolean;
  moleculeType?: string;
  timeline?: { at: number; action?: string; alpha?: number }[];
  [key: string]: any;
}

export interface RawScene {
  id?: string;
  startTime?: number;
  duration?: number;
  learningGoal?: string;   // plain-English teaching objective
  focus?: string;
  text?: string;
  actors?: RawActor[];
  sequence?: SequenceEvent[];   // timed event list (new)
  animations?: AnimationLink[];
  environment?: string;
  meta?: Record<string, any>;
  [key: string]: any;
}

export interface RawScript {
  title?: string;
  duration?: number;
  concept?: string;
  cognitive_level?: string;
  cognitive_load?: string;
  scenes?: RawScene[];
  [key: string]: any;
}

export interface NormalizedActor extends RawActor {
  id: string;
  type: string;
  role: string;
  x: number | null;
  y: number | null;
  animation: string;
  color: string;
  size: number;
  text: string;
  fontSize: number;
  rays: boolean;
  moleculeType: string;
  timeline: { at: number; action?: string; alpha?: number }[];
}

export interface NormalizedScene {
  id: string;
  startTime: number;
  duration: number;
  learningGoal: string;        // plain-English teaching objective
  focus: string;
  text: string;
  actors: NormalizedActor[];
  sequence: SequenceEvent[];   // staggered timed events
  animations: AnimationLink[];
  environment: string;
  meta: Record<string, any>;
}

export interface NormalizedScript {
  title: string;
  duration: number;
  concept: string;
  cognitive_level: string;
  scenes: NormalizedScene[];
}

const DEFAULT_SCENE_DURATION = 6000;
const warnings: string[] = [];

const DEFAULT_COLORS: Record<string, string> = {
  sun: "#FACC15",
  plant: "#4CAF50",
  leaf: "#4CAF50",
  root: "#6D4C41",
  cloud: "#FFFFFF",
  water: "#29B6F6",
  waterdrop: "#29B6F6",
  co2: "#90A4AE",
  oxygen: "#22C55E",
  glucose: "#FB923C",
  bolt: "#A855F7",
  arrow: "#1565C0",
  rock: "#795548",
  planet: "#42A5F5",
  volcano: "#6D4C41",
  label: "#2563EB",
  thermometer: "#EF4444",
  bulb: "#FACC15",
  ear: "#F59E0B",
  molecule: "#29B6F6",
  animal: "#D9A56F",
  battery: "#FACC15",
  switch: "#CBD5E1",
  wire: "#FACC15",
  wave: "#2563EB",
};

const TYPE_ALIAS: Record<string, string> = {
  water_drop: "waterdrop",
  droplet: "waterdrop",
  h2o: "waterdrop",
  carbon_dioxide: "co2",
  carbondioxide: "co2",
  // 'oxygen' and 'o2' map to 'oxygen' actor type (do NOT map to molecule)
  o2: "oxygen",
  glucose_molecule: "glucose",
  lightning: "bolt",
  energy: "bolt",
  tree: "plant",
  leaves: "leaf",
  roots: "root",
  conductor: "wire",
  circuit: "wire",
  battery_cell: "battery",
  lamp: "bulb",
  vibration: "wave",
  sound_wave: "wave",
  star: "sun",
  // NOTE: 'cell' is a valid biology actor type — do NOT alias it to molecule
};

function warn(message: string) {
  warnings.push(message);
  try {
    if (typeof __DEV__ !== "undefined" && __DEV__) {
      console.warn(`[ScriptNormalizer] ${message}`);
    }
  } catch {
    // no-op
  }
}

function cleanType(type: any): string {
  const raw = String(type || "label").trim().toLowerCase();
  const normalized = raw.replace(/\s+/g, "_");
  return TYPE_ALIAS[normalized] || normalized;
}

function parseNumeric(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function normalizeTimeline(raw: any): { at: number; action?: string; alpha?: number }[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((step) => step && Number.isFinite(step.at))
    .map((step) => ({
      at: Math.max(0, Number(step.at)),
      action: step.action ? String(step.action) : undefined,
      alpha: typeof step.alpha === "number" ? step.alpha : undefined,
    }))
    .sort((a, b) => a.at - b.at);
}

/**
 * Nudge actors that share the same slot (legacy scripts / edge cases) so the canvas
 * does not stack sprites. Server-side layout is primary; this is a safety pass only.
 */
function deoverlapActorXY(actors: NormalizedActor[]) {
  const minSep = 28;
  for (let i = 0; i < actors.length; i += 1) {
    for (let j = i + 1; j < actors.length; j += 1) {
      const a = actors[i];
      const b = actors[j];
      if (a.x == null || b.x == null || a.y == null || b.y == null) continue;
      if (Math.abs(a.x - b.x) < minSep && Math.abs(a.y - b.y) < minSep) {
        b.x = b.x + minSep;
      }
    }
  }
}

function normalizeActor(raw: RawActor, index: number, sceneId: string): NormalizedActor {
  const type = cleanType(raw.type);
  const timeline = normalizeTimeline(raw.timeline);

  const x = parseNumeric(raw.x);
  const y = parseNumeric(raw.y);
  if (x == null || y == null) {
    warn(`Scene "${sceneId}" actor[${index}] "${type}" is missing x/y. Auto-layout will place it.`);
  }

  const rawSize = parseNumeric(raw.size);
  const rawFont = parseNumeric(raw.fontSize);
  const size = rawSize == null
    ? 40
    : rawSize > 0 && rawSize <= 1.2
      ? rawSize
      : Math.max(8, Math.min(260, rawSize));

  // Generate stable id if missing (backend v2 always provides one)
  const id = String(raw.id || `${type}_${index}`);

  return {
    ...raw,
    id,
    type,
    role: String(raw.role || ""),
    x,
    y,
    animation: String(raw.animation || "appear").toLowerCase().trim(),
    color: String(raw.color || DEFAULT_COLORS[type] || DEFAULT_COLORS.label),
    size,
    text: String(raw.text || ""),
    fontSize: rawFont != null && rawFont > 0 ? rawFont : 14,
    rays: raw.rays === true,
    moleculeType: String(raw.moleculeType || ""),
    timeline,
  };
}

function normalizeAnimationLinks(raw: any[]): AnimationLink[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((a) => a && typeof a === "object" && a.from && a.to)
    .map((a) => ({
      type: String(a.type || "flow"),
      from: String(a.from),
      to: String(a.to),
      duration: typeof a.duration === "number" ? a.duration : undefined,
      direction: a.direction != null ? String(a.direction) : undefined,
    }));
}

function normalizeSequence(raw: any): SequenceEvent[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((e) => e && typeof e === "object" && typeof e.time === "number" && e.target)
    .map((e) => ({
      time:      Math.max(0, Number(e.time)),
      action:    String(e.action || "appear"),
      target:    String(e.target),
      to:        e.to && typeof e.to === "object" ? e.to : undefined,
      to_target: e.to_target ? String(e.to_target) : undefined,
      value:     e.value,
    }))
    .sort((a, b) => a.time - b.time);
}

function normalizeScene(raw: RawScene, index: number, fallbackStart: number): NormalizedScene {
  const id = String(raw.id || `scene_${index}`);
  const duration =
    Number.isFinite(raw.duration) && Number(raw.duration) > 0
      ? Number(raw.duration)
      : DEFAULT_SCENE_DURATION;
  const startTime =
    Number.isFinite(raw.startTime) && Number(raw.startTime) >= 0
      ? Number(raw.startTime)
      : fallbackStart;
  const actors = Array.isArray(raw.actors)
    ? raw.actors.map((actor, actorIndex) => normalizeActor(actor || {}, actorIndex, id))
    : [];
  deoverlapActorXY(actors);

  const rawFocus = String(raw.focus || "").trim();
  const rawText = String(raw.text || "").trim();
  const focus = rawFocus
    ? rawFocus.split(" ").slice(0, 5).join(" ")
    : rawText.split(" ").slice(0, 5).join(" ");
  const learningGoal = String(raw.learningGoal || focus || "").trim();
  const sequence = normalizeSequence(raw.sequence);

  if (actors.length === 0 && rawText) {
    warn(`Scene "${id}" has narration text but no visual actors.`);
  }

  return {
    id,
    startTime,
    duration,
    learningGoal,
    focus,
    text: rawText.split(" ").slice(0, 5).join(" "),
    actors,
    sequence,
    animations: normalizeAnimationLinks(raw.animations || []),
    environment: String(raw.environment || "").toLowerCase().trim(),
    meta: raw.meta && typeof raw.meta === "object" ? raw.meta : {},
  };
}

function createFallbackScript(title = "Untitled Animation"): NormalizedScript {
  return {
    title,
    concept: title,
    duration: DEFAULT_SCENE_DURATION,
    cognitive_level: "medium",
    scenes: [
      {
        id: "fallback_scene",
        startTime: 0,
        duration: DEFAULT_SCENE_DURATION,
        focus: "Loading animation",
        text: "Animation data is loading...",
        actors: [],
        animations: [],
        environment: "minimal",
        meta: {},
      },
    ],
  };
}

export function normalizeScript(raw: RawScript | any): NormalizedScript {
  warnings.length = 0;

  if (!raw || typeof raw !== "object") {
    warn("Invalid script payload received. Generated fallback scene.");
    return createFallbackScript();
  }

  const title = String(raw.title || "Untitled Animation");
  const concept = String(raw.concept || raw.title || "");
  // Support both cognitive_level (v2) and cognitive_load (v1)
  const cognitive_level = String(
    raw.cognitive_level || raw.cognitive_load || "medium"
  ).toLowerCase();
  const rawScenes = Array.isArray(raw.scenes) ? raw.scenes : [];

  if (rawScenes.length === 0) {
    warn("Script has no scenes. Generated fallback scene.");
    return createFallbackScript(title);
  }

  const scenes: NormalizedScene[] = [];
  let fallbackStart = 0;

  for (let i = 0; i < rawScenes.length; i += 1) {
    const scene = normalizeScene(rawScenes[i] || {}, i, fallbackStart);
    scenes.push(scene);
    fallbackStart = scene.startTime + scene.duration;
  }

  scenes.sort((a, b) => a.startTime - b.startTime);

  // Fill missing/overlapping start times after sort.
  let currentStart = 0;
  for (let i = 0; i < scenes.length; i += 1) {
    if (!Number.isFinite(scenes[i].startTime) || scenes[i].startTime < currentStart) {
      scenes[i].startTime = currentStart;
    }
    currentStart = scenes[i].startTime + scenes[i].duration;
  }

  const computedDuration = scenes.reduce(
    (max, scene) => Math.max(max, scene.startTime + scene.duration),
    0,
  );
  const duration =
    Number.isFinite(raw.duration) && Number(raw.duration) > 0
      ? Math.max(Number(raw.duration), computedDuration)
      : computedDuration;

  return { title, concept, duration, cognitive_level, scenes };
}

export function getLastNormalizationWarnings(): string[] {
  return [...warnings];
}

declare let __DEV__: boolean | undefined;
