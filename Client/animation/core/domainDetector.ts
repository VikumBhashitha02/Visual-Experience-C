/**
 * animation/core/domainDetector.ts
 * Strong domain detection covering the full Grade 6 science syllabus.
 * Specific domains beat generic ones; electric_circuit beats broad "energy".
 */

export type ConceptDomain =
  // Life science
  | "photosynthesis"
  | "respiration"
  | "food_chain"
  | "human_body"
  // Physical science
  | "electric_circuit"
  | "sound"
  | "heat_transfer"
  | "gravity"
  | "solar_system"
  // Earth science
  | "water_cycle"
  // Fallback
  | "generic";

export type DomainVisualTheme = {
  backgroundTop: string;
  backgroundBottom: string;
  accent: string;
  ground?: string;
};

type DomainSignal = {
  keyword: string;
  weight: number;
};

type DomainScore = {
  domain: ConceptDomain;
  score: number;
};

// ── Keyword signal tables ──────────────────────────────────────────────────────
// Weights > 3.0 = very strong match; 2.0–3.0 = strong; 1.0–2.0 = moderate
const DOMAIN_SIGNALS: Record<ConceptDomain, DomainSignal[]> = {
  // ── PHOTOSYNTHESIS ────────────────────────────────────────────────────────
  photosynthesis: [
    { keyword: "photosynthesis", weight: 4.0 },
    { keyword: "chlorophyll", weight: 3.5 },
    { keyword: "chloroplast", weight: 3.5 },
    { keyword: "plant food", weight: 3.0 },
    { keyword: "stomata", weight: 3.0 },
    { keyword: "glucose", weight: 2.4 },
    { keyword: "carbon dioxide", weight: 2.0 },
    { keyword: "co2", weight: 1.8 },
    { keyword: "oxygen", weight: 1.5 },  // shared with respiration but lower weight here
    { keyword: "leaf", weight: 1.2 },
    { keyword: "sunlight", weight: 1.2 },
    { keyword: "light energy", weight: 1.8 },
  ],

  // ── WATER CYCLE ───────────────────────────────────────────────────────────
  water_cycle: [
    { keyword: "water cycle", weight: 4.0 },
    { keyword: "evaporation", weight: 3.0 },
    { keyword: "condensation", weight: 3.0 },
    { keyword: "precipitation", weight: 3.0 },
    { keyword: "transpiration", weight: 2.8 },
    { keyword: "water vapor", weight: 2.5 },
    { keyword: "water vapour", weight: 2.5 },
    { keyword: "cloud formation", weight: 2.5 },
    { keyword: "rainfall", weight: 1.8 },
    { keyword: "rain", weight: 1.4 },
    { keyword: "cloud", weight: 1.2 },
    { keyword: "runoff", weight: 2.0 },
    { keyword: "water sources", weight: 1.8 },
    { keyword: "water conservation", weight: 1.8 },
    { keyword: "water salinity", weight: 1.6 },
    { keyword: "flood", weight: 1.6 },
    { keyword: "drought", weight: 1.6 },
    { keyword: "states of water", weight: 2.2 },
  ],

  // ── FOOD CHAIN ────────────────────────────────────────────────────────────
  food_chain: [
    { keyword: "food chain", weight: 4.0 },
    { keyword: "food web", weight: 3.8 },
    { keyword: "producer", weight: 2.2 },
    { keyword: "consumer", weight: 2.2 },
    { keyword: "herbivore", weight: 2.4 },
    { keyword: "carnivore", weight: 2.4 },
    { keyword: "predator", weight: 2.0 },
    { keyword: "prey", weight: 1.8 },
    { keyword: "ecosystem", weight: 1.6 },
    { keyword: "ecosystem balance", weight: 2.4 },
    { keyword: "food habits", weight: 2.0 },
    { keyword: "trophic", weight: 2.2 },
  ],

  // ── ELECTRIC CIRCUIT ─────────────────────────────────────────────────────
  electric_circuit: [
    { keyword: "electric circuit", weight: 4.5 },
    { keyword: "simple circuit", weight: 4.2 },
    { keyword: "series circuit", weight: 4.0 },
    { keyword: "parallel circuit", weight: 4.0 },
    { keyword: "circuit diagram", weight: 3.8 },
    { keyword: "circuit", weight: 2.6 },
    { keyword: "battery", weight: 2.8 },
    { keyword: "bulb", weight: 2.8 },
    { keyword: "switch", weight: 2.6 },
    { keyword: "wire", weight: 2.2 },
    { keyword: "current", weight: 2.2 },
    { keyword: "conductor", weight: 1.8 },
    { keyword: "insulator", weight: 1.8 },
    { keyword: "electricity", weight: 2.0 },
    { keyword: "voltage", weight: 2.0 },
    { keyword: "resistor", weight: 2.0 },
    { keyword: "electron", weight: 1.8 },
    { keyword: "electric", weight: 1.6 },
    { keyword: "complete circuit", weight: 3.5 },
    { keyword: "incomplete circuit", weight: 3.5 },
    { keyword: "current flow", weight: 2.8 },
    { keyword: "magnet", weight: 1.5 },  // ch7-8 overlap
    { keyword: "magnetic", weight: 1.5 },
    { keyword: "electromagnet", weight: 2.0 },
    { keyword: "generating electricity", weight: 3.0 },
  ],

  // ── SOUND ─────────────────────────────────────────────────────────────────
  sound: [
    { keyword: "sound", weight: 2.8 },
    { keyword: "vibration", weight: 2.8 },
    { keyword: "vibrate", weight: 2.5 },
    { keyword: "hearing", weight: 2.4 },
    { keyword: "ear", weight: 2.0 },
    { keyword: "noise", weight: 1.8 },
    { keyword: "echo", weight: 2.0 },
    { keyword: "wave", weight: 1.8 },
    { keyword: "frequency", weight: 2.0 },
    { keyword: "pitch", weight: 2.0 },
    { keyword: "music", weight: 1.6 },
    { keyword: "instrument", weight: 1.6 },
    { keyword: "loud", weight: 1.4 },
    { keyword: "soft sound", weight: 1.8 },
    { keyword: "sound production", weight: 2.4 },
    { keyword: "how we hear", weight: 2.4 },
  ],

  // ── HEAT TRANSFER ─────────────────────────────────────────────────────────
  heat_transfer: [
    { keyword: "heat transfer", weight: 4.0 },
    { keyword: "heat", weight: 2.2 },
    { keyword: "temperature", weight: 2.4 },
    { keyword: "thermal", weight: 2.0 },
    { keyword: "conduction", weight: 2.6 },
    { keyword: "convection", weight: 2.6 },
    { keyword: "radiation", weight: 2.2 },
    { keyword: "thermometer", weight: 2.2 },
    { keyword: "hot", weight: 1.4 },
    { keyword: "cold", weight: 1.4 },
    { keyword: "heat expansion", weight: 2.8 },
    { keyword: "change of state", weight: 2.2 },
    { keyword: "melting", weight: 2.0 },
    { keyword: "boiling", weight: 2.0 },
    { keyword: "heat and colour", weight: 2.2 },
    { keyword: "sources of heat", weight: 2.2 },
    { keyword: "measuring temperature", weight: 2.4 },
  ],

  // ── GRAVITY ───────────────────────────────────────────────────────────────
  gravity: [
    { keyword: "gravity", weight: 4.0 },
    { keyword: "gravitational", weight: 3.5 },
    { keyword: "weight", weight: 2.2 },
    { keyword: "fall", weight: 2.0 },
    { keyword: "drop", weight: 1.8 },
    { keyword: "pull", weight: 1.8 },
    { keyword: "earth pulls", weight: 2.8 },
    { keyword: "attraction", weight: 1.6 },
    { keyword: "free fall", weight: 2.5 },
    { keyword: "mass", weight: 1.4 },
  ],

  // ── SOLAR SYSTEM ─────────────────────────────────────────────────────────
  solar_system: [
    { keyword: "solar system", weight: 4.2 },
    { keyword: "planet", weight: 2.6 },
    { keyword: "orbit", weight: 2.5 },
    { keyword: "moon", weight: 2.0 },
    { keyword: "asteroid", weight: 2.2 },
    { keyword: "galaxy", weight: 2.4 },
    { keyword: "star", weight: 1.4 },
    { keyword: "earth", weight: 1.4 },
    { keyword: "mars", weight: 2.0 },
    { keyword: "jupiter", weight: 2.0 },
    { keyword: "mercury", weight: 2.0 },
    { keyword: "revolution", weight: 1.8 },
    { keyword: "rotation", weight: 1.8 },
    { keyword: "milky way", weight: 2.4 },
    { keyword: "space", weight: 1.2 },
    { keyword: "cosmos", weight: 1.6 },
    { keyword: "comet", weight: 2.0 },
  ],

  // ── RESPIRATION ───────────────────────────────────────────────────────────
  respiration: [
    { keyword: "respiration", weight: 4.0 },
    { keyword: "breathing", weight: 3.0 },
    { keyword: "inhalation", weight: 2.8 },
    { keyword: "exhalation", weight: 2.8 },
    { keyword: "lungs", weight: 2.5 },
    { keyword: "oxygen", weight: 1.8 },
    { keyword: "carbon dioxide", weight: 2.0 },
    { keyword: "exhale", weight: 2.6 },
    { keyword: "inhale", weight: 2.6 },
    { keyword: "diaphragm", weight: 2.2 },
  ],

  // ── HUMAN BODY ────────────────────────────────────────────────────────────
  human_body: [
    { keyword: "heart", weight: 2.5 },
    { keyword: "blood", weight: 2.2 },
    { keyword: "circulation", weight: 2.6 },
    { keyword: "digestive", weight: 2.4 },
    { keyword: "muscle", weight: 1.8 },
    { keyword: "skeleton", weight: 2.0 },
    { keyword: "body system", weight: 2.4 },
    { keyword: "nervous", weight: 2.2 },
    { keyword: "organ", weight: 1.8 },
    { keyword: "bone", weight: 1.8 },
    { keyword: "brain", weight: 2.0 },
    { keyword: "stomach", weight: 2.0 },
    { keyword: "immune", weight: 2.0 },
    { keyword: "human body", weight: 3.0 },
    { keyword: "pulse", weight: 2.0 },
  ],

  // ── GENERIC (always 0) ────────────────────────────────────────────────────
  generic: [],
};

// ── Visual themes ──────────────────────────────────────────────────────────────
export const DOMAIN_VISUALS: Record<ConceptDomain, DomainVisualTheme> = {
  photosynthesis: {
    backgroundTop: "#A8E6A1",
    backgroundBottom: "#DFF7D8",
    accent: "#2E7D32",
    ground: "#795548",
  },
  water_cycle: {
    backgroundTop: "#9EDBFF",
    backgroundBottom: "#E2F5FF",
    accent: "#0288D1",
    ground: "#8D6E63",
  },
  food_chain: {
    backgroundTop: "#C9EFA5",
    backgroundBottom: "#F4FCE8",
    accent: "#558B2F",
    ground: "#7F5539",
  },
  electric_circuit: {
    backgroundTop: "#1E3A8A",
    backgroundBottom: "#111827",
    accent: "#FACC15",
  },
  sound: {
    backgroundTop: "#CFE8FF",
    backgroundBottom: "#EFF6FF",
    accent: "#2563EB",
  },
  heat_transfer: {
    backgroundTop: "#FFD6A5",
    backgroundBottom: "#FFEFD5",
    accent: "#EA580C",
  },
  gravity: {
    backgroundTop: "#BBDEFB",
    backgroundBottom: "#E3F2FD",
    accent: "#1D4ED8",
    ground: "#6D4C41",
  },
  solar_system: {
    backgroundTop: "#0F172A",
    backgroundBottom: "#1E1B4B",
    accent: "#60A5FA",
  },
  respiration: {
    backgroundTop: "#FFD9E8",
    backgroundBottom: "#FFF1F7",
    accent: "#E11D48",
  },
  human_body: {
    backgroundTop: "#FDE68A",
    backgroundBottom: "#FFF7CC",
    accent: "#DC2626",
  },
  generic: {
    backgroundTop: "#B5D9FF",
    backgroundBottom: "#ECF6FF",
    accent: "#2563EB",
    ground: "#7C5A45",
  },
};

// ── Internal helpers ───────────────────────────────────────────────────────────
function buildSources(title: string, scenes: any[]): {
  title: string;
  sceneText: string;
  actorHints: string;
} {
  const sceneText = Array.isArray(scenes)
    ? scenes.map((scene) => String(scene?.text || "")).join(" ").toLowerCase()
    : "";
  const actorHints = Array.isArray(scenes)
    ? scenes
      .map((scene) =>
        Array.isArray(scene?.actors)
          ? scene.actors.map((actor: any) => String(actor?.type || "")).join(" ")
          : "",
      )
      .join(" ")
      .toLowerCase()
    : "";
  return {
    title: String(title || "").toLowerCase(),
    sceneText,
    actorHints,
  };
}

function containsKeyword(corpus: string, keyword: string): boolean {
  if (!keyword.trim()) return false;
  if (keyword.includes(" ")) return corpus.includes(keyword);
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`\\b${escaped}\\b`, "i");
  return pattern.test(corpus);
}

function scoreDomain(domain: ConceptDomain, title: string, scenes: any[]): number {
  if (domain === "generic") return 0;
  const sources = buildSources(title, scenes);
  const signals = DOMAIN_SIGNALS[domain] || [];
  let score = 0;

  for (const signal of signals) {
    // Scene text is most authoritative, then title, then actor type hints
    if (containsKeyword(sources.sceneText, signal.keyword)) score += signal.weight * 1.6;
    if (containsKeyword(sources.title, signal.keyword)) score += signal.weight * 1.1;
    if (containsKeyword(sources.actorHints, signal.keyword)) score += signal.weight * 0.45;
  }

  // ── Hard-lock checks ──────────────────────────────────────────────────────
  // Electric circuit: battery+bulb+(wire|switch|circuit) is definitive
  const electricHard =
    (containsKeyword(sources.sceneText, "battery") || containsKeyword(sources.title, "battery")) &&
    (containsKeyword(sources.sceneText, "bulb") || containsKeyword(sources.title, "bulb")) &&
    (containsKeyword(sources.sceneText, "wire") ||
      containsKeyword(sources.sceneText, "switch") ||
      containsKeyword(sources.sceneText, "circuit"));

  // Photosynthesis: needs plant process + plant structure
  const photoHard =
    (containsKeyword(sources.sceneText, "photosynthesis") ||
      containsKeyword(sources.sceneText, "chlorophyll") ||
      containsKeyword(sources.sceneText, "chloroplast")) &&
    (containsKeyword(sources.sceneText, "plant") ||
      containsKeyword(sources.sceneText, "leaf") ||
      containsKeyword(sources.actorHints, "plant") ||
      containsKeyword(sources.actorHints, "leaf"));

  if (domain === "electric_circuit" && electricHard) score += 9.0;
  if (domain === "photosynthesis" && photoHard) score += 7.0;

  // Photosynthesis must have BOTH plant context AND process context or gets penalised
  if (domain === "photosynthesis") {
    const plantContext =
      containsKeyword(sources.sceneText, "plant") ||
      containsKeyword(sources.sceneText, "leaf") ||
      containsKeyword(sources.actorHints, "plant") ||
      containsKeyword(sources.actorHints, "leaf");
    const processContext =
      containsKeyword(sources.sceneText, "photosynthesis") ||
      containsKeyword(sources.sceneText, "chlorophyll") ||
      containsKeyword(sources.sceneText, "chloroplast") ||
      containsKeyword(sources.sceneText, "co2") ||
      containsKeyword(sources.sceneText, "carbon dioxide") ||
      containsKeyword(sources.sceneText, "glucose");
    if (!(plantContext && processContext)) score -= 3.5;
  }

  // Prevent domain contamination
  if (domain === "photosynthesis" && electricHard) score -= 10.0;
  if (domain === "electric_circuit" && photoHard) score -= 5.0;
  if (domain === "solar_system" && photoHard) score -= 4.0;
  if (domain === "photosynthesis" && containsKeyword(sources.sceneText, "solar system")) score -= 3.0;

  // Respiration vs photosynthesis disambiguation
  if (domain === "respiration") {
    const respContext =
      containsKeyword(sources.sceneText, "breathing") ||
      containsKeyword(sources.sceneText, "lungs") ||
      containsKeyword(sources.sceneText, "inhale") ||
      containsKeyword(sources.sceneText, "exhale") ||
      containsKeyword(sources.sceneText, "respiration");
    if (!respContext) score -= 2.0;
  }

  // Human body vs respiration: body systems check
  if (domain === "human_body") {
    const bodyContext =
      containsKeyword(sources.sceneText, "heart") ||
      containsKeyword(sources.sceneText, "blood") ||
      containsKeyword(sources.sceneText, "digestive") ||
      containsKeyword(sources.sceneText, "skeleton") ||
      containsKeyword(sources.sceneText, "muscle") ||
      containsKeyword(sources.sceneText, "nervous") ||
      containsKeyword(sources.sceneText, "brain");
    if (!bodyContext) score -= 1.5;
  }

  return score;
}

export function detectDomain(title: string, scenes: any[]): ConceptDomain {
  const corpus = buildSources(title, scenes);
  const allText = `${corpus.title} ${corpus.sceneText} ${corpus.actorHints}`;
  if (!allText.trim()) return "generic";

  // Priority tiebreak order (for nearly equal scores)
  const priority: ConceptDomain[] = [
    "electric_circuit",
    "photosynthesis",
    "water_cycle",
    "food_chain",
    "sound",
    "heat_transfer",
    "gravity",
    "solar_system",
    "respiration",
    "human_body",
    "generic",
  ];

  const scored: DomainScore[] = (Object.keys(DOMAIN_SIGNALS) as ConceptDomain[])
    .filter((domain) => domain !== "generic")
    .map((domain) => ({
      domain,
      score: scoreDomain(domain, title, scenes),
    }))
    .filter((entry) => entry.score > 0.3)
    .sort((a, b) => {
      if (Math.abs(a.score - b.score) > 0.25) return b.score - a.score;
      return priority.indexOf(a.domain) - priority.indexOf(b.domain);
    });

  if (!scored.length) return "generic";
  // Require a meaningful score – avoid labelling everything as a domain
  if (scored[0].score < 2.6) return "generic";
  return scored[0].domain;
}
