"""
Rule-Based Engine — Stage 2 of the redesigned pipeline.

Converts a visual_plan (from visual_planner.py) into a fully-specified
animation script that the frontend can render without any ambiguity.

Pipeline:
  visual_plan → rule_engine → animation_script

Deterministic only: syllabi actions (evaporation → rise motion on water, etc.) map to
renderer animations here — never guess layout from free text on the client.
"""
import logging
import re
from typing import Any, Optional

from app.services.visual.grade6_syllabus import topic_visual_pattern

logger = logging.getLogger(__name__)

# ─── Canvas bounds ────────────────────────────────────────────────────────────
CANVAS_W = 800
CANVAS_H = 600
X_MIN, X_MAX = 60, 740
Y_MIN, Y_MAX = 60, 540

# ─── Semantic color palette ───────────────────────────────────────────────────
COLORS = {
    "sun":           "#FFD700",
    "star":          "#FFE066",
    "plant":         "#2E7D32",
    "leaf":          "#43A047",
    "root":          "#795548",
    "cell":          "#66BB6A",
    "bacteria":      "#AED581",
    "animal":        "#FF8A65",
    "molecule_water":"#2196F3",
    "molecule_co2":  "#9E9E9E",
    "molecule_o2":   "#81C784",
    "molecule_magma":"#FF5722",
    "molecule_sediment":"#8D6E63",
    "molecule_rock": "#78909C",
    "glucose":       "#FF9800",
    "earth":         "#1565C0",
    "moon":          "#90A4AE",
    "planet":        "#42A5F5",
    "asteroid":      "#A1887F",
    "comet":         "#ECEFF1",
    "ocean":         "#1565C0",
    "cloud":         "#ECEFF1",
    "mountain":      "#6D4C41",
    "volcano":       "#B71C1C",
    "rock":          "#78909C",
    "atom":          "#CE93D8",
    "electron":      "#FFEB3B",
    "proton":        "#EF5350",
    "neutron":       "#90A4AE",
    "arrow":         "#FFFFFF",
    "label":         "#FFFFFF",
    "line":          "#FFFFFF",
    "bolt":          "#FFD740",
    "wave":          "#9C27B0",
    "thermometer":   "#EF5350",
    "graph":         "#64B5F6",
    "number":        "#FFFFFF",
}

# Brighter / “activated” tints for targets after interaction (visual meaning).
COLOR_ACTIVE: dict[str, str] = {
    "sun":            "#FFF9C4",
    "star":           "#FFFDE7",
    "plant":          "#66BB6A",
    "leaf":           "#A5D6A7",
    "root":           "#A1887F",
    "molecule_water": "#4DD0E1",
    "molecule_co2":   "#E0E0E0",
    "molecule_o2":    "#C8E6C9",
    "glucose":        "#FFCC80",
    "cloud":          "#E3F2FD",
    "ocean":          "#29B6F6",
    "rock":           "#B0BEC5",
    "bolt":           "#FFEE58",
    "cell":           "#A5D6A7",
}

# Each teaching beat repeats within the scene timeline (client uses modulo).
# High / “overload” tier: fewer repeats — deeper single pass per scene.
LOOP_COUNT_BY_LOAD = {"low": 3, "medium": 2, "high": 1}

# Slower “full picture” recap: one long segment, fewer repeats.
SUMMARY_SEGMENT_MS = {"low": 17000, "medium": 14000, "high": 11000}
SUMMARY_LOOP_COUNT = {"low": 2, "medium": 2, "high": 1}

# Micro-pauses (holdMs on timeline + tail slowdown on client).
_PAUSE_HOLD_PRIMARY_MS = {"low": 520, "medium": 340, "high": 280}
_PAUSE_HOLD_SECONDARY_MS = {"low": 450, "medium": 280, "high": 230}
_SEGMENT_TAIL_PAUSE_MS = {"low": 560, "medium": 460, "high": 380}
# Emphasis timing: quiet beat before semantic action, settle beat after (see also tail pause).
PRE_ACTION_PAUSE_MS = 400
POST_ACTION_PAUSE_MS = 500


def _segment_tail_pause_ms(cognitive_load: str) -> int:
    """Tail slowdown at end of each loop segment — at least post-action pause."""
    base = _SEGMENT_TAIL_PAUSE_MS.get(cognitive_load, 400)
    return max(base, POST_ACTION_PAUSE_MS)

# ─── Semantic position map (role → x, y as fractions of canvas) ──────────────
# Positions encode MEANING: sun top-right, plant center, root bottom, etc.
POSITIONS = {
    "sun":            (0.88, 0.14),
    "star":           (0.88, 0.14),
    "cloud":          (0.30, 0.16),
    "moon":           (0.70, 0.28),
    "planet":         (0.50, 0.50),
    "earth":          (0.50, 0.80),
    "asteroid":       (0.20, 0.20),
    "comet":          (0.15, 0.15),
    "plant":          (0.36, 0.62),
    "leaf":           (0.36, 0.45),
    "root":           (0.36, 0.82),
    "cell":           (0.50, 0.50),
    "bacteria":       (0.45, 0.50),
    "animal":         (0.60, 0.65),
    "molecule_water": (0.25, 0.70),
    "molecule_co2":   (0.72, 0.28),
    "molecule_o2":    (0.68, 0.20),
    "molecule_magma": (0.70, 0.72),
    "molecule_sediment":(0.50,0.88),
    "molecule_rock":  (0.55, 0.60),
    "glucose":        (0.55, 0.48),
    "ocean":          (0.50, 0.88),
    "mountain":       (0.72, 0.55),
    "volcano":        (0.72, 0.62),
    "rock":           (0.50, 0.30),
    "atom":           (0.50, 0.50),
    "electron":       (0.60, 0.40),
    "proton":         (0.50, 0.50),
    "neutron":        (0.50, 0.52),
    "arrow":          (0.50, 0.50),
    "label":          (0.50, 0.30),
    "line":           (0.50, 0.50),
    "bolt":           (0.50, 0.44),
    "wave":           (0.50, 0.50),
    "thermometer":    (0.80, 0.50),
    "graph":          (0.50, 0.40),
    "number":         (0.50, 0.35),
}

# ─── Actor type normaliser (element names → canonical actor types) ─────────────
ELEMENT_TO_ACTOR = {
    "sun":              "sun",
    "star":             "star",
    "cloud":            "cloud",
    "moon":             "moon",
    "planet":           "planet",
    "earth":            "earth",
    "asteroid":         "asteroid",
    "comet":            "comet",
    "plant":            "plant",
    "leaf":             "leaf",
    "root":             "root",
    "cell":             "cell",
    "bacteria":         "bacteria",
    "animal":           "animal",
    "molecule_water":   "molecule",
    "molecule_co2":     "molecule",
    "molecule_o2":      "molecule",
    "molecule_magma":   "molecule",
    "molecule_sediment":"molecule",
    "molecule_rock":    "molecule",
    "glucose":          "glucose",
    "ocean":            "ocean",
    "mountain":         "mountain",
    "volcano":          "volcano",
    "rock":             "rock",
    "atom":             "atom",
    "electron":         "electron",
    "proton":           "proton",
    "neutron":          "neutron",
    "light_ray":        "arrow",
    "arrow":            "arrow",
    "label":            "label",
    "line":             "line",
    "bolt":             "bolt",
    "wave":             "wave",
    "thermometer":      "thermometer",
    "graph":            "graph",
    "number":           "number",
}

MOLECULE_TYPES = {
    "molecule_water":    "water",
    "molecule_co2":      "co2",
    "molecule_o2":       "o2",
    "molecule_magma":    "magma",
    "molecule_sediment": "sediment",
    "molecule_rock":     "rock",
}

# ─── Animation mapping (action + element role → animation) ───────────────────
def _pick_animation(element: str, action: str, is_cause: bool, is_effect: bool) -> str:
    """Deterministic animation: syllabus verbs override generic verb logic."""
    action_n = _normalize_action(action)

    # Grade 6 science — fixed metaphors (water cycle, plants, energy)
    if action_n == "evaporation":
        if element == "molecule_water":
            return "bubbleUp"
        if element == "sun":
            return "shine"
        if element == "ocean":
            return "glow"
        if element == "cloud":
            return "sway"
    if action_n == "condensation":
        if element == "cloud":
            return "grow"
        if element == "molecule_water":
            return "floatIn"
    if action_n == "precipitation":
        if element == "molecule_water":
            return "fall"
        if element == "cloud":
            return "pulse"
    if action_n in ("rise",):
        if element == "molecule_water":
            return "bubbleUp"
    if action_n == "photosynthesis":
        if element == "leaf":
            return "glow"
        if element == "plant":
            return "glow"
        if element in ("molecule_co2", "molecule_water"):
            return "floatIn"
        if element == "molecule_o2":
            return "floatOut"
        if element == "glucose":
            return "appear"
        if element == "sun":
            return "shine"
    if action_n == "respiration":
        if element == "molecule_o2":
            return "floatIn"
        if element == "molecule_co2":
            return "floatOut"
        if element == "leaf":
            return "pulse"
    if action_n == "rotate":
        if element == "wave":
            return "rotate"
        if element == "bolt":
            return "pulse"
        if element == "cloud":
            return "sway"
    if action_n == "energy_transfer":
        if element == "bolt":
            return "pulse"
        if element == "wave":
            return "wave"
        if element == "thermometer":
            return "pulse"
        if element == "sun":
            return "shine"
        if element == "rock":
            return "glow"

    ELEMENT_ANIMS = {
        "sun":       "shine",
        "star":      "shine",
        "bolt":      "pulse",
        "glucose":   "appear",
        "electron":  "rotate",
        "wave":      "wave",
        "volcano":   "pulse",
        "root":      "absorb",
        "cloud":     "sway",
        "leaf":      "glow",
        "cell":      "pulse",
        "bacteria":  "pulse",
    }
    if element in ELEMENT_ANIMS and action_n not in (
        "emit", "flow", "absorb", "transform", "appear", "grow",
    ):
        return ELEMENT_ANIMS[element]

    if action_n in ("emit", "flow", "attract"):
        if is_cause:
            if element in ("earth", "planet", "moon"):
                return "pulse"
            if element == "sun":
                return "shine"
            return "glow"
        if is_effect:
            if element == "ocean":
                return "glow"
            mol_map = {
                "molecule_water": "bubbleUp",
                "molecule_co2": "floatIn",
                "molecule_o2": "floatOut",
                "molecule_magma": "bubbleUp",
            }
            return mol_map.get(element, "pulse")

    if action_n == "absorb":
        return "absorb" if is_effect else "pulse"

    if action_n == "transform":
        return "glow" if is_cause else "grow"

    if action_n in ("parallel", "system", "feedback", "cycle"):
        return "pulse"

    if action_n == "grow":
        return "grow"
    if action_n == "appear":
        return "appear"
    if action_n == "fall":
        return "fall" if element == "molecule_water" else "moveDown"

    if element in ELEMENT_ANIMS:
        return ELEMENT_ANIMS[element]

    if element in ("arrow", "light_ray"):
        return "appear"

    return "idle"


# ─── Size rules per cognitive level ──────────────────────────────────────────
def _actor_size(element: str, cognitive_load: str, n_elements: int, is_cause: bool) -> int:
    """
    LOW:    huge single actors (80–100)
    MEDIUM: medium actors (50–75), cause bigger than effect
    HIGH:   smaller actors (30–55) to fit more on screen
    """
    base_sizes = {
        "low":    {"primary": 95,  "secondary": 80,  "label": 0,  "arrow": 0},
        "medium": {"primary": 70,  "secondary": 55,  "label": 0,  "arrow": 0},
        "high":   {"primary": 50,  "secondary": 38,  "label": 0,  "arrow": 0},
    }
    cfg = base_sizes.get(cognitive_load, base_sizes["medium"])

    if element in ("label","number","graph"):
        return 0   # labels have fontSize, not size
    if element in ("arrow","line","light_ray"):
        return 0   # arrows have length

    if n_elements == 1:
        sz = cfg["primary"]
    elif is_cause:
        sz = cfg["primary"]
    else:
        sz = cfg["secondary"]

    if cognitive_load == "high" and n_elements >= 4:
        sz = int(sz * 0.88)
    return sz


# ─── Scene timing per cognitive level ─────────────────────────────────────────
# Segment length per tier: LOW = brisk beats + many scenes; HIGH = long breakdown.
SCENE_DURATIONS = {
    "low":    10500,
    "medium": 6200,
    "high":   8200,
}

# Client playback (animation clock). LOW feels faster; HIGH slower / more inspect time.
PLAYBACK_SPEED = {"low": 1.2, "medium": 1.0, "high": 0.8}

# Cross-fade between scenes (ms): LOW = snappy; HIGH = gentler handoff.
SCENE_TRANSITION_MS = {"low": 220, "medium": 400, "high": 520}

# Intra-scene: secondary / support actors appear after primary (ms).
_SECONDARY_APPEAR_DELAY_MS = {
    "low":    3600,
    "medium": 1800,
    "high":   1000,
}
_SUPPORT_APPEAR_EXTRA_MS = 720

def _slot_fraction(index: int, total: int) -> tuple[float, float]:
    """Deterministic slots — up to 5 actors (overload tier) in two loose rows."""
    if total <= 1:
        return (0.50, 0.48)
    if total == 2:
        return [(0.26, 0.48), (0.74, 0.48)][min(index, 1)]
    if total == 3:
        return [(0.20, 0.48), (0.50, 0.48), (0.80, 0.48)][min(index, 2)]
    if total == 4:
        slots = [(0.22, 0.36), (0.78, 0.36), (0.22, 0.60), (0.78, 0.60)]
        return slots[min(index, 3)]
    slots = [(0.18, 0.34), (0.50, 0.32), (0.82, 0.34), (0.34, 0.62), (0.66, 0.62)]
    return slots[min(index, 4)]


def _resolve_position(index: int, total: int, cognitive_load: str) -> tuple[int, int]:
    """Pixel position from slot index — semantic element names do not move layout."""
    _ = cognitive_load
    fx, fy = _slot_fraction(index, total)
    x = int(fx * CANVAS_W)
    y = int(fy * CANVAS_H)
    return (max(X_MIN, min(X_MAX, x)), max(Y_MIN, min(Y_MAX, y)))


def _flow_direction(action_n: str) -> str:
    """Hints for frontend flow curves (vertical vs horizontal emphasis)."""
    if action_n in ("evaporation", "rise"):
        return "up"
    if action_n in ("precipitation", "fall"):
        return "down"
    if action_n in ("transform", "photosynthesis", "respiration"):
        return "transform"
    if action_n == "condensation":
        return "up"
    return "along"


def _normalize_action(raw: str) -> str:
    """Map synonyms / LLM variants to canonical verbs used by _pick_animation."""
    s = (raw or "appear").strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    synonyms = {
        "rotation": "rotate",
        "vaporization": "evaporation",
        "rain": "precipitation",
        "raining": "precipitation",
        "rainfall": "precipitation",
        "photosynth": "photosynthesis",
        "heat_transfer": "energy_transfer",
        "radiation": "emit",
        "conduction": "energy_transfer",
        "convection": "flow",
    }
    return synonyms.get(s, s)


# ─── Learning goal templates ──────────────────────────────────────────────────
_LEARNING_GOALS = {
    "appear":    "Introduce {subject} as the key element",
    "grow":      "Show {subject} growing in response to conditions",
    "emit":      "Show how {cause} sends energy to {effect}",
    "flow":      "Show how material flows from {cause} to {effect}",
    "absorb":    "Show {effect} taking in material from the environment",
    "transform": "Show {cause} converting into {effect}",
    "evaporation": "Show water changing to vapor and rising",
    "condensation": "Show vapor cooling to form clouds",
    "precipitation": "Show water falling from clouds",
    "photosynthesis": "Show how light drives food-making in the leaf",
    "respiration": "Show gas exchange in the leaf",
    "energy_transfer": "Show energy moving from {cause} to {effect}",
    "parallel":  "Show multiple processes happening simultaneously",
    "system":    "See the full system with all parts active",
    "feedback":  "Understand how {effect} feeds back into {cause}",
    "cycle":     "See the complete cycle from start to finish",
    "glow":      "See {subject} becoming active and energised",
}

def _build_learning_goal(action: str, cause_elem: str | None,
                          effect_elem: str | None, elements: list[str]) -> str:
    """Generate a plain-English learning goal for this scene."""
    template = _LEARNING_GOALS.get(action, "Observe {subject} in action")
    subject = (elements[0] if elements else "element").replace("molecule_", "")
    cause   = (cause_elem  or "source").replace("molecule_", "")
    effect  = (effect_elem or "target").replace("molecule_", "")
    return template.format(subject=subject, cause=cause, effect=effect)


# ─── Sequence builder ─────────────────────────────────────────────────────────
# Each actor appears at a staggered offset, then performs its semantic action.
# This guarantees sequential visual events — never a "screen dump" of actors.

_STAGGER_MS = {
    "low":    2200,
    "medium": 700,
    "high":   380,
}

def _five_words(text: str) -> str:
    """Short on-screen copy — teaching is visual first."""
    w = (text or "").split()
    return " ".join(w[:5]).strip()


def _intra_scene_timeline(
    emphasis: str,
    cognitive_load: str,
    *,
    is_summary: bool = False,
) -> list[dict[str, Any]]:
    """Primary first → pause → secondary/support; holdMs adds micro-pauses after entrance."""
    pri_ms = 520 if is_summary else 450
    sd = _SECONDARY_APPEAR_DELAY_MS.get(cognitive_load, 1400)
    fade = 560 if is_summary else 520
    hold_p = _PAUSE_HOLD_PRIMARY_MS.get(cognitive_load, 300) + (240 if is_summary else 0)
    hold_s = _PAUSE_HOLD_SECONDARY_MS.get(cognitive_load, 240) + (200 if is_summary else 0)
    if emphasis == "primary":
        return [
            {"at": 0, "alpha": 0},
            {"at": pri_ms, "alpha": 1, "easing": "easeOut", "holdMs": hold_p},
        ]
    if emphasis == "secondary":
        return [
            {"at": 0, "alpha": 0},
            {"at": sd, "alpha": 0},
            {"at": sd + fade, "alpha": 1, "easing": "easeOut", "holdMs": hold_s},
        ]
    extra = sd + _SUPPORT_APPEAR_EXTRA_MS
    return [
        {"at": 0, "alpha": 0},
        {"at": extra, "alpha": 0},
        {"at": extra + fade, "alpha": 1, "easing": "easeOut", "holdMs": hold_s},
    ]


_ACTION_OFFSETS = {
    # After appear: how many ms before the semantic action fires
    "shine":    400,
    "glow":     600,
    "pulse":    500,
    "bubbleUp": 700,
    "floatIn":  700,
    "floatOut": 700,
    "absorb":   800,
    "grow":     600,
    "rotate":   400,
    "wave":     400,
    "sway":     500,
        "orbit":    600,
        "rotate":   500,
        "idle":     0,
        "appear":   0,
}

def _build_sequence(
    actors: list[dict],
    cause_id: str | None,
    effect_id: str | None,
    action: str,
    cognitive_load: str,
    duration: int,
    secondary_entrance_ms: int = 0,
) -> list[dict]:
    """
    Build a timed sequence[] for the scene.

    Structure per actor:
      t=0 + stagger*i  → appear
      t=appear + offset → semantic animation action

    For emit/flow/absorb: add a final 'emit'/'flow'/'absorb' event
    linking cause_id → effect_id after all actors have appeared.
    """
    n_act = len(actors)
    stagger = _STAGGER_MS.get(cognitive_load, 600)
    if n_act >= 4:
        stagger = int(stagger * 1.38)
    if n_act >= 5:
        stagger = int(stagger * 1.12)
    sequence: list[dict] = []
    pre = PRE_ACTION_PAUSE_MS

    for i, actor in enumerate(actors):
        actor_id  = actor.get("id", f"actor_{i}")
        actor_anim = actor.get("animation", "idle")
        appear_at  = i * stagger

        # 1. Appear event
        sequence.append({"time": appear_at, "action": "appear", "target": actor_id})

        # 2. Semantic animation event (skip for pure appear/idle)
        if actor_anim not in ("appear", "idle"):
            offset    = _ACTION_OFFSETS.get(actor_anim, 500)
            action_at = min(appear_at + offset + pre, duration - 320)
            sequence.append({"time": action_at, "action": actor_anim, "target": actor_id})

    # 3. Cause → effect flow event (meaningful actions only)
    an = _normalize_action(action)
    if cause_id and effect_id and an in (
        "emit", "flow", "absorb", "transform", "attract", "repel",
        "evaporation", "condensation", "precipitation", "photosynthesis",
        "respiration", "energy_transfer", "fall", "rise", "rotate",
    ):
        base = n_act * stagger + 200 + pre
        flow_at = min(max(base, secondary_entrance_ms + 480 + pre // 2), int(duration * 0.72))
        sequence.append({
            "time":      flow_at,
            "action":    an,
            "target":    cause_id,
            "to_target": effect_id,
        })

    # Sort by time so frontend can walk the list in order
    sequence.sort(key=lambda e: e["time"])
    return sequence


def _first_semantic_action_end_ms(
    sequence: list[dict],
    actor_id: str,
    segment_duration: int,
) -> int | None:
    """When the actor’s own motion (not flow link) has largely finished — ‘after’ state starts."""
    for e in sequence:
        if e.get("target") != actor_id or e.get("to_target"):
            continue
        act = str(e.get("action") or "")
        if act in ("", "appear"):
            continue
        t = int(e["time"])
        return min(t + 520, segment_duration - 80)
    return None


def _apply_visual_state_timing(
    actors: list[dict],
    elements: list[str],
    sequence: list[dict],
    scene_animations: list[dict],
    segment_duration: int,
    sd_all: int,
) -> None:
    """
    Before/after clarity: colorActive + reactAfterMs on every teaching actor.
    Single-actor: state flips after local animation; multi-actor: tied to flow completion.
    """
    if not actors:
        return

    flow_ev = next((e for e in sequence if e.get("to_target")), None)
    fdur = int(scene_animations[0]["duration"]) if scene_animations else int(segment_duration * 0.38)
    ft = int(flow_ev["time"]) if flow_ev else None

    def active_for(i: int) -> str:
        el = elements[i] if i < len(elements) else None
        return COLOR_ACTIVE.get(el, "#E3F2FD") if el else "#E3F2FD"

    if len(elements) == 1:
        for i, a in enumerate(actors):
            if a.get("type") == "label":
                continue
            a["colorActive"] = active_for(i)
            a["stateChange"] = True
            aid = str(a.get("id") or "")
            end = _first_semantic_action_end_ms(sequence, aid, segment_duration)
            if end is None:
                end = min(1200, segment_duration - 280)
            a["reactAfterMs"] = end
        return

    for i, a in enumerate(actors):
        if a.get("type") == "label":
            continue
        em = a.get("emphasis")
        a["colorActive"] = active_for(i)

        if ft is None:
            aid = str(a.get("id") or "")
            end = _first_semantic_action_end_ms(sequence, aid, segment_duration)
            if end is None:
                end = min(sd_all + 1400, segment_duration - 120)
            if em == "secondary":
                a["targetReaction"] = True
            else:
                a["stateChange"] = True
            a["reactAfterMs"] = end
            continue

        if em == "secondary":
            a["targetReaction"] = True
            a["reactAfterMs"] = min(ft + int(fdur * 0.38), segment_duration - 80)
        elif em == "primary":
            a["stateChange"] = True
            a["reactAfterMs"] = min(ft + int(fdur * 0.58), segment_duration - 60)
        else:
            a["stateChange"] = True
            a["reactAfterMs"] = min(ft + int(fdur * 0.52), segment_duration - 70)


# ─── Core converter ───────────────────────────────────────────────────────────

def _unit_to_scene(
    unit: dict,
    scene_index: int,
    start_time: int,
    cognitive_load: str,
    syllabus_topic: str | None = None,
) -> dict:
    """Convert one visual_unit into one fully-specified scene."""
    u = dict(unit)
    if syllabus_topic and "_syllabus_topic" not in u:
        u["_syllabus_topic"] = syllabus_topic
    unit = u
    unit_id    = unit.get("id", f"unit_{scene_index + 1}")
    idea       = unit.get("idea", "")
    elements   = unit.get("elements", [])
    action     = unit.get("action", "appear")
    cause_elem = unit.get("cause")
    effect_elem = unit.get("effect")
    action_n   = _normalize_action(action)

    is_summary = bool(unit.get("is_summary"))
    segment_duration = SCENE_DURATIONS.get(cognitive_load, 6000)
    if is_summary:
        segment_duration = SUMMARY_SEGMENT_MS.get(cognitive_load, 14000)
        loop_count = SUMMARY_LOOP_COUNT.get(cognitive_load, 2)
    else:
        loop_count = LOOP_COUNT_BY_LOAD.get(cognitive_load, 2)
    total_duration = int(segment_duration * max(1, loop_count))

    # Cognitive tier actor caps: LOW 1–2, OPTIMAL 2–3, OVERLOAD/high 3–5 layered.
    max_elements = {"low": 2, "medium": 3, "high": 5}.get(cognitive_load, 3)
    elements = (elements or [])[:max_elements]

    # Infer cause/effect whenever two or more entities appear (all cognitive levels)
    if len(elements) >= 2:
        if not cause_elem:
            cause_elem = elements[0]
        if not effect_elem:
            effect_elem = elements[1]

    actors: list[dict] = []
    actor_ids_by_element: dict[str, str] = {}

    for i, element in enumerate(elements):
        actor_type = ELEMENT_TO_ACTOR.get(element, "label")
        is_cause   = (element == cause_elem)
        is_effect  = (element == effect_elem)
        # Stable id: must match scene.animations[].from / to for flow lines
        actor_id   = f"s{scene_index:02d}_{element}_{i}"
        actor_ids_by_element[element] = actor_id

        x, y = _resolve_position(i, len(elements), cognitive_load)
        size  = _actor_size(element, cognitive_load, len(elements), is_cause)
        color = COLORS.get(element, "#FFFFFF")
        anim  = _pick_animation(element, action, is_cause, is_effect)
        if anim == "idle" and actor_type != "label":
            if is_cause:
                anim = "shine" if element == "sun" else "glow"
            elif is_effect:
                anim = "pulse"
            else:
                anim = "sway"

        if action_n == "transform" and is_effect and actor_type != "label":
            anim = "transform"
        elif action_n in ("rise", "evaporation") and element == "molecule_water":
            anim = "rise"
        elif action_n in ("fall", "precipitation") and element == "molecule_water":
            anim = "fall"

        emphasis = "primary"
        if len(elements) >= 2:
            emphasis = "primary" if is_cause else ("secondary" if is_effect else "support")
        elif len(elements) == 1:
            emphasis = "primary"

        actor: dict[str, Any] = {
            "id":        actor_id,
            "type":      actor_type,
            "role":      "cause" if is_cause else ("effect" if is_effect else "context"),
            "emphasis":  emphasis,
            "x":         x,
            "y":         y,
            "size":      size,
            "color":     color,
            "animation": anim,
            "timeline":  _intra_scene_timeline(emphasis, cognitive_load, is_summary=is_summary),
        }

        # Type-specific fields
        if actor_type == "molecule" and element in MOLECULE_TYPES:
            actor["moleculeType"] = MOLECULE_TYPES[element]
        if actor_type == "sun":
            actor["rays"] = True
        if actor_type == "label":
            actor["text"]     = idea[:20]
            actor["fontSize"] = 16
            actor.pop("size", None)
        if actor_type == "arrow":
            actor["angle"]     = 0.0
            actor["length"]    = 100
            actor["thickness"] = 3
            actor.pop("size", None)

        actors.append(actor)

    sd_all = _SECONDARY_APPEAR_DELAY_MS.get(cognitive_load, 1400)
    flow_start_ms = sd_all + 360 if len(elements) >= 2 else 0
    if len(actors) >= 2:
        for a in actors:
            em = a.get("emphasis")
            if em == "primary":
                a["motionHoldUntilMs"] = sd_all + 240
            elif em == "support":
                a["motionHoldUntilMs"] = sd_all + _SUPPORT_APPEAR_EXTRA_MS + 240

    # ── animations[] process links (no extra arrow actor — avoids overlap clutter)
    scene_animations: list[dict] = []
    cause_id  = actor_ids_by_element.get(cause_elem) if cause_elem else None
    effect_id = actor_ids_by_element.get(effect_elem) if effect_elem else None

    if len(elements) >= 2 and cause_id and effect_id:
        flow_type = action_n if action_n in (
            "emit", "flow", "absorb", "transform", "orbit", "attract", "repel",
            "evaporation", "condensation", "precipitation", "photosynthesis",
            "respiration", "energy_transfer", "fall", "rise", "rotate",
        ) else "flow"
        scene_animations.append({
            "type":      flow_type,
            "from":      cause_id,
            "to":        effect_id,
            "duration":  int(segment_duration * 0.7),
            "direction": _flow_direction(flow_type),
        })

    # ── sequence[] — staggered timed events ───────────────────────────────────
    sequence = _build_sequence(
        actors, cause_id, effect_id, action, cognitive_load, segment_duration,
        secondary_entrance_ms=sd_all,
    )

    _apply_visual_state_timing(
        actors, elements, sequence, scene_animations, segment_duration, sd_all,
    )

    # ── learningGoal (short; visuals carry teaching) ──────────────────────────
    learning_goal = _five_words(_build_learning_goal(action_n, cause_elem, effect_elem, elements))

    # ── focus / text: max 5 words ─────────────────────────────────────────────
    focus = _five_words(idea)
    if is_summary:
        focus = _five_words("Whole picture together")

    def _lbl(x: str | None) -> str:
        return (x or "part").replace("molecule_", "")

    captions = {
        "emit":           "Energy moves to target",
        "flow":           "Material flows along",
        "absorb":         "Material enters here",
        "transform":      "One form becomes another",
        "evaporation":    "Water vapor rises up",
        "condensation":   "Vapor forms visible clouds",
        "precipitation":  "Rain falls downward",
        "photosynthesis": "Leaf traps light energy",
        "respiration":    "Gases swap in the leaf",
        "energy_transfer": "Heat moves along matter",
        "grow":           _five_words(f"{_lbl(elements[0] if elements else 'part')} grows larger"),
        "appear":         _five_words(f"{_lbl(elements[0] if elements else 'part')} appears here"),
        "system":         "Many parts work together",
        "parallel":       "Processes run together",
        "feedback":       "Output loops back around",
        "cycle":          "Steps repeat as a cycle",
    }
    text = _five_words(captions.get(action_n, focus))
    if len(elements) == 1 and not is_summary:
        text = focus
    if is_summary:
        text = focus

    st = str(unit.get("_syllabus_topic") or "").strip()
    vt = topic_visual_pattern(st) if st else "process"

    focus_actor_id = None
    for a in actors:
        if a.get("emphasis") == "primary":
            focus_actor_id = a.get("id")
            break
    if not focus_actor_id and actors:
        focus_actor_id = actors[0].get("id")

    tail_pause = _segment_tail_pause_ms(cognitive_load)
    scene_out = {
        "id":           unit_id,
        "startTime":    start_time,
        "duration":     total_duration,
        "learningGoal": learning_goal,
        "focus":        focus,
        "text":         text,
        "actors":       actors,
        "sequence":     sequence,
        "animations":   scene_animations,
        "meta":           {
            "pipeline": "rule_engine",
            "cognitive_load": cognitive_load,
            "syllabus_topic": unit.get("_syllabus_topic"),
            "visual_pattern": vt,
            "focus_actor_id": focus_actor_id,
            "one_idea":       True,
            "flow_start_ms":  flow_start_ms,
            "secondary_entrance_ms": sd_all if len(elements) >= 2 else 0,
            "loop_segment_ms": segment_duration,
            "loop_count":      loop_count,
            "segment_tail_pause_ms": tail_pause,
            "is_summary":      is_summary,
            "playback_speed":  PLAYBACK_SPEED.get(cognitive_load, 1.0),
            "scene_transition_ms": SCENE_TRANSITION_MS.get(cognitive_load, 400),
        },
    }
    _log_animation_link_integrity(unit_id, actors, scene_animations)
    return scene_out


def _log_animation_link_integrity(
    unit_id: str,
    actors: list[dict],
    scene_animations: list[dict],
) -> None:
    """Debug: flow lines must reference actor ids present in this scene."""
    ids = {a.get("id") for a in actors if a.get("id")}
    for an in scene_animations:
        fid, tid = an.get("from"), an.get("to")
        if fid not in ids or tid not in ids:
            logger.warning(
                "[rule_engine] Animation link mismatch scene=%s from=%r to=%r valid_ids=%s",
                unit_id, fid, tid, sorted(ids),
            )


def _collect_unique_elements(units: list[dict], max_n: int = 3) -> list[str]:
    """Gather up to max_n distinct element tokens from units (for recap scene)."""
    seen: set[str] = set()
    out: list[str] = []
    for u in units:
        if not isinstance(u, dict) or u.get("is_summary"):
            continue
        for el in u.get("elements") or []:
            s = str(el).strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
            if len(out) >= max_n:
                return out
    return out


def _make_summary_unit(
    concept: str,
    units: list[dict],
    *,
    max_unique_elements: int = 4,
) -> Optional[dict[str, Any]]:
    if len(units) < 2:
        return None
    els = _collect_unique_elements(units, max_unique_elements)
    if len(els) < 2:
        return None
    return {
        "id": "summary",
        "is_summary": True,
        "idea": _five_words(concept or "Science"),
        "elements": els,
        "action": "cycle",
    }


# ─── Public API ───────────────────────────────────────────────────────────────

def plan_to_script(visual_plan: dict) -> dict:
    """
    Convert a visual_plan dict (from visual_planner.py) into a
    complete, frontend-ready animation script dict.

    Every scene now contains:
      - learningGoal  : plain-English teaching objective
      - focus         : ≤6-word visual caption
      - text          : 1-sentence description
      - actors        : fully-specified actor list
      - sequence      : staggered timed events (appear → action → cause→effect)
      - animations    : process-flow links between actor IDs
    """
    concept       = visual_plan.get("concept", "Concept")
    cognitive_load = visual_plan.get("cognitive_load", "medium").lower()
    units         = visual_plan.get("visual_units", [])

    scenes: list[dict] = []
    current_start = 0

    syllabus_topic = visual_plan.get("syllabus_topic")

    for i, unit in enumerate(units):
        scene = _unit_to_scene(unit, i, current_start, cognitive_load, syllabus_topic=syllabus_topic)
        scenes.append(scene)
        current_start += scene["duration"]

    summary_cap = {"low": 3, "medium": 4, "high": 5}.get(cognitive_load, 4)
    summary_unit = _make_summary_unit(concept, units, max_unique_elements=summary_cap)
    if summary_unit:
        sum_scene = _unit_to_scene(
            summary_unit,
            len(scenes),
            current_start,
            cognitive_load,
            syllabus_topic=syllabus_topic,
        )
        scenes.append(sum_scene)
        current_start += sum_scene["duration"]

    script: dict[str, Any] = {
        "title":          concept,
        "cognitive_level": cognitive_load,
        "cognitive_load":  cognitive_load,
        "duration":        current_start,
        "scenes":          scenes,
        "meta": {
            "pipeline": "rule_engine",
            "syllabus_topic": syllabus_topic,
            "domain": visual_plan.get("domain"),
            "playback_speed": PLAYBACK_SPEED.get(cognitive_load, 1.0),
            "scene_transition_ms": SCENE_TRANSITION_MS.get(cognitive_load, 400),
        },
    }
    cg = visual_plan.get("concept_graph")
    if isinstance(cg, dict):
        script["concept_graph"] = cg

    logger.info("[rule_engine] Script built: %d scenes, %dms total for '%s' [%s]",
                len(scenes), current_start, concept, cognitive_load)
    return script


def visual_plan_to_script(concept: str, cognitive_load: str = "medium",
                           domain: Optional[str] = None) -> dict:
    """
    Full two-stage pipeline:
      1. visual_planner.build_visual_plan  → visual_plan
      2. plan_to_script                    → animation_script
    """
    from app.services.visual.visual_planner import build_visual_plan
    visual_plan = build_visual_plan(concept, cognitive_load, domain)
    return plan_to_script(visual_plan)

