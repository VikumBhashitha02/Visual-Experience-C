"""
Grade 6 Science — syllabus topic detection and canonical visual plans.

The LLM may only suggest short visual_units; this module:
  - Maps free-text concepts to a syllabus topic
  - Supplies deterministic fallback visual_units when the model is off-topic or fails
  - Whitelists element tokens per topic (aligned to rule_engine.ELEMENT_TO_ACTOR)

Topics covered (India / international Grade 6 science core):
  water_cycle, energy, solar_energy, wind_energy, plant_processes
"""
from __future__ import annotations

import re
from typing import Any

# Topic ids used internally
SYLLABUS_TOPICS = frozenset({
    "water_cycle",
    "energy",
    "solar_energy",
    "wind_energy",
    "plant_processes",
})

# Keywords → topic (first match in iteration order wins for overlapping sets)
_TOPIC_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("water_cycle", (
        "water cycle", "hydrologic", "evaporation", "condensation", "precipitation",
        "water vapour", "water vapor", "runoff", "collection", "infiltration",
    )),
    ("plant_processes", (
        "photosynthesis", "chlorophyll", "respiration", "plant process", "stomata",
        "transpiration", "leaf food", "make food",
    )),
    ("solar_energy", (
        "solar energy", "solar panel", "photovoltaic", "sun power", "solar cell",
        "solar cooker", "solar heater",
    )),
    ("wind_energy", (
        "wind energy", "windmill", "wind turbine", "wind power", "turbine",
    )),
    ("energy", (
        "energy", "heat", "temperature", "thermal", "transfer of heat",
        "conduction", "convection", "radiation", "fuel", "power",
    )),
]


def topic_visual_pattern(topic: str) -> str:
    """
    Map syllabus topic to a Grade 6 visual pattern for layouts / teacher UX.
    """
    t = (topic or "").strip().lower()
    mapping = {
        "water_cycle": "cycle",
        "plant_processes": "process",
        "energy": "energy_flow",
        "solar_energy": "energy_flow",
        "wind_energy": "energy_flow",
    }
    return mapping.get(t, "process")


def detect_syllabus_topic(concept: str) -> str:
    """Return the closest Grade 6 syllabus topic id for navigation / fallback plans."""
    c = (concept or "").strip().lower()
    if not c:
        return "energy"
    for topic, keys in _TOPIC_KEYWORDS:
        if any(k in c for k in keys):
            return topic
    # Loose token matches
    if re.search(r"\bwater\b", c) and re.search(r"\b(cycle|cloud|rain|vapor|vapour)\b", c):
        return "water_cycle"
    if "plant" in c or "leaf" in c:
        return "plant_processes"
    return "energy"


# Allowed planner element tokens per topic (subset of visual_planner / rule_engine vocab)
_ALLOWED_ELEMENTS: dict[str, frozenset[str]] = {
    "water_cycle": frozenset({
        "sun", "ocean", "cloud", "mountain", "molecule_water", "arrow", "label",
    }),
    "energy": frozenset({
        "sun", "rock", "thermometer", "bolt", "arrow", "label", "wave", "earth",
    }),
    "solar_energy": frozenset({
        "sun", "bolt", "plant", "arrow", "label", "earth",
    }),
    "wind_energy": frozenset({
        "cloud", "wave", "bolt", "arrow", "label", "plant",
    }),
    "plant_processes": frozenset({
        "sun", "plant", "leaf", "root", "molecule_water", "molecule_co2", "molecule_o2",
        "glucose", "arrow", "label", "bolt",
    }),
}


def allowed_elements(topic: str) -> frozenset[str]:
    return _ALLOWED_ELEMENTS.get(topic, _ALLOWED_ELEMENTS["energy"])


# Deterministic fallback visual_units per topic × cognitive load (short ideas, ≤3 elements each)
_FALLBACK_UNITS: dict[str, dict[str, list[dict[str, Any]]]] = {
    "water_cycle": {
        "low": [
            {"id": "u1", "idea": "Sun heats water", "elements": ["sun"], "action": "evaporation"},
            {"id": "u2", "idea": "Water rises as vapor", "elements": ["molecule_water"], "action": "evaporation"},
            {"id": "u3", "idea": "Clouds form", "elements": ["cloud"], "action": "condensation"},
            {"id": "u4", "idea": "Rain falls down", "elements": ["molecule_water"], "action": "precipitation"},
            {"id": "u5", "idea": "Water returns to ocean", "elements": ["ocean"], "action": "flow"},
        ],
        "medium": [
            {"id": "u1", "idea": "Sun warms ocean water", "elements": ["sun", "ocean"], "action": "evaporation"},
            {"id": "u2", "idea": "Vapor rises and cools", "elements": ["molecule_water", "cloud"], "action": "condensation"},
            {"id": "u3", "idea": "Rain falls to earth", "elements": ["cloud", "molecule_water"], "action": "precipitation"},
            {"id": "u4", "idea": "Water flows downhill", "elements": ["mountain", "ocean"], "action": "flow"},
        ],
        "high": [
            {"id": "u1", "idea": "Energy drives water cycle", "elements": ["sun", "ocean", "cloud"], "action": "energy_transfer"},
            {"id": "u2", "idea": "Evaporation and condensation", "elements": ["molecule_water", "cloud"], "action": "evaporation"},
            {"id": "u3", "idea": "Precipitation completes cycle", "elements": ["cloud", "ocean"], "action": "precipitation"},
        ],
    },
    "plant_processes": {
        "low": [
            {"id": "u1", "idea": "Sun gives light", "elements": ["sun"], "action": "emit"},
            {"id": "u2", "idea": "Roots take water", "elements": ["root"], "action": "absorb"},
            {"id": "u3", "idea": "Leaf makes food", "elements": ["leaf"], "action": "photosynthesis"},
            {"id": "u4", "idea": "Oxygen is released", "elements": ["molecule_o2"], "action": "emit"},
        ],
        "medium": [
            {"id": "u1", "idea": "Light reaches leaf", "elements": ["sun", "leaf"], "action": "emit"},
            {"id": "u2", "idea": "Water moves up plant", "elements": ["root", "leaf"], "action": "flow"},
            {"id": "u3", "idea": "CO2 enters leaf", "elements": ["molecule_co2", "leaf"], "action": "absorb"},
            {"id": "u4", "idea": "Sugar and oxygen made", "elements": ["glucose", "molecule_o2"], "action": "photosynthesis"},
        ],
        "high": [
            {"id": "u1", "idea": "Inputs enter leaf", "elements": ["sun", "molecule_co2", "molecule_water"], "action": "photosynthesis"},
            {"id": "u2", "idea": "Leaf produces outputs", "elements": ["leaf", "glucose", "molecule_o2"], "action": "transform"},
        ],
    },
    "energy": {
        "low": [
            {"id": "u1", "idea": "Heat source appears", "elements": ["sun"], "action": "emit"},
            {"id": "u2", "idea": "Objects warm up", "elements": ["rock"], "action": "glow"},
            {"id": "u3", "idea": "Heat moves along", "elements": ["arrow"], "action": "energy_transfer"},
        ],
        "medium": [
            {"id": "u1", "idea": "Sun radiates energy", "elements": ["sun", "bolt"], "action": "emit"},
            {"id": "u2", "idea": "Energy flows to matter", "elements": ["bolt", "rock"], "action": "energy_transfer"},
            {"id": "u3", "idea": "Temperature can rise", "elements": ["thermometer", "rock"], "action": "transform"},
        ],
        "high": [
            {"id": "u1", "idea": "Energy transfer system", "elements": ["sun", "bolt", "rock"], "action": "energy_transfer"},
            {"id": "u2", "idea": "Heat spreads in materials", "elements": ["rock", "wave"], "action": "flow"},
        ],
    },
    "solar_energy": {
        "low": [
            {"id": "u1", "idea": "Sunlight arrives", "elements": ["sun"], "action": "emit"},
            {"id": "u2", "idea": "Energy becomes electricity", "elements": ["bolt"], "action": "appear"},
        ],
        "medium": [
            {"id": "u1", "idea": "Sun gives solar energy", "elements": ["sun", "bolt"], "action": "emit"},
            {"id": "u2", "idea": "Power flows to use", "elements": ["bolt", "arrow"], "action": "flow"},
        ],
        "high": [
            {"id": "u1", "idea": "Solar energy path", "elements": ["sun", "bolt", "plant"], "action": "energy_transfer"},
        ],
    },
    "wind_energy": {
        "low": [
            {"id": "u1", "idea": "Moving air", "elements": ["cloud"], "action": "appear"},
            {"id": "u2", "idea": "Wind does work", "elements": ["bolt"], "action": "pulse"},
        ],
        "medium": [
            {"id": "u1", "idea": "Wind carries energy", "elements": ["cloud", "bolt"], "action": "flow"},
            {"id": "u2", "idea": "Turbine turns", "elements": ["wave", "bolt"], "action": "rotate"},
        ],
        "high": [
            {"id": "u1", "idea": "Wind to electricity", "elements": ["cloud", "wave", "bolt"], "action": "energy_transfer"},
        ],
    },
}


def get_fallback_visual_units(topic: str, cognitive_load: str) -> list[dict[str, Any]]:
    """Pure rule-based visual units for the syllabus topic (no LLM)."""
    load = cognitive_load.lower() if cognitive_load else "medium"
    if load not in ("low", "medium", "high"):
        load = "medium"
    table = _FALLBACK_UNITS.get(topic) or _FALLBACK_UNITS["energy"]
    return [dict(u) for u in table.get(load, table["medium"])]


def _sanitize_elements(topic: str, elements: list[Any]) -> list[str]:
    allow = allowed_elements(topic)
    out: list[str] = []
    for el in elements or []:
        s = str(el).strip().lower().replace(" ", "_").replace("-", "_")
        if s in allow and s not in out:
            out.append(s)
    return out


def validate_and_fix_visual_plan(concept: str, plan: dict[str, Any], cognitive_load: str) -> dict[str, Any]:
    """
    Enforce syllabus alignment. Accepted shapes:

      A) { "concept", "steps": ["...", ...] }  — LLM concept extraction only; graph built in-code.
      B) { "concept", "visual_units": [...] } — legacy / rule-only plans.

    Strips unknown keys from units. Replaces empty plans with syllabus fallback.
    """
    effective_concept = str(plan.get("concept") or concept or "").strip()
    topic = detect_syllabus_topic(effective_concept)
    load = (cognitive_load or "medium").lower()
    if load not in ("low", "medium", "high"):
        load = "medium"

    concept_graph: dict[str, Any] | None = plan.get("concept_graph")  # type: ignore[assignment]

    raw_units_early = plan.get("visual_units")
    has_llm_units = (
        isinstance(raw_units_early, list)
        and len(raw_units_early) > 0
        and any(isinstance(u, dict) and (u.get("elements") or u.get("idea")) for u in raw_units_early)
    )

    raw_steps = plan.get("steps")
    if not has_llm_units and isinstance(raw_steps, list) and len(raw_steps) > 0:
        from app.services.visual.concept_graph import build_graph_and_visual_units

        step_strings = [str(s).strip() for s in raw_steps if str(s).strip()]
        if step_strings:
            vu, concept_graph = build_graph_and_visual_units(effective_concept, step_strings, load)
            plan = {**plan, "visual_units": vu}

    raw_units = plan.get("visual_units")
    fixed_units: list[dict[str, Any]] = []

    if isinstance(raw_units, list):
        for i, u in enumerate(raw_units):
            if not isinstance(u, dict):
                continue
            idea = str(u.get("idea", "")).strip()
            words = idea.split()
            if len(words) > 5:
                idea = " ".join(words[:5])
            action = str(u.get("action", "appear")).strip().lower().replace(" ", "_")
            els = _sanitize_elements(topic, u.get("elements") or [])
            max_el = {"low": 2, "medium": 3, "high": 5}.get(load, 3)
            els = els[:max_el]
            # Avoid mixing unrelated syllabus topics when LLM copy points elsewhere.
            ut = detect_syllabus_topic(f"{effective_concept} {idea}")
            if (
                len(idea) > 10
                and ut != topic
                and ut in SYLLABUS_TOPICS
                and topic in SYLLABUS_TOPICS
            ):
                fb_list = get_fallback_visual_units(topic, load)
                if i < len(fb_list):
                    fb = fb_list[i]
                    idea = str(fb.get("idea", idea)).strip()
                    words_i = idea.split()
                    if len(words_i) > 5:
                        idea = " ".join(words_i[:5])
                    action = str(fb.get("action", action)).strip().lower().replace(" ", "_")
                    els = _sanitize_elements(topic, fb.get("elements") or [])[:max_el]
            if not idea:
                idea = f"Step {i + 1}"
            if not els:
                continue
            fixed_units.append({
                "id": str(u.get("id") or f"unit_{i + 1}"),
                "idea": idea,
                "elements": els,
                "action": action,
            })

    max_units = {"low": 7, "medium": 6, "high": 4}.get(load, 6)
    if not fixed_units:
        fixed_units = get_fallback_visual_units(topic, load)

    fixed_units = fixed_units[:max_units]

    out: dict[str, Any] = {
        "concept": effective_concept or str(plan.get("concept") or concept).strip(),
        "domain": "grade6_science",
        "syllabus_topic": topic,
        "cognitive_load": load,
        "visual_units": fixed_units,
    }
    if concept_graph is not None:
        out["concept_graph"] = concept_graph
    return out


def build_rule_only_visual_plan(concept: str, cognitive_load: str = "medium") -> dict[str, Any]:
    """Syllabus-only visual plan (deterministic, no model call)."""
    topic = detect_syllabus_topic(concept)
    load = cognitive_load.lower() if cognitive_load else "medium"
    return {
        "concept": (concept or "").strip() or topic.replace("_", " "),
        "domain": "grade6_science",
        "syllabus_topic": topic,
        "cognitive_load": load,
        "visual_units": get_fallback_visual_units(topic, load),
    }


def _infer_action_from_text(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ("evaporat", "vapor", "steam")):
        return "evaporation"
    if any(k in low for k in ("condens", "cloud form", "cool")):
        return "condensation"
    if any(k in low for k in ("rain", "snow", "precipitat", "fall")):
        return "precipitation"
    if any(k in low for k in ("photosynth", "chlorophyll", "glucose", "oxygen")):
        return "photosynthesis"
    if any(k in low for k in ("respiration", "breathe", "carbon dioxide")):
        return "respiration"
    if any(k in low for k in ("heat", "energy transfer", "warm", "radiat")):
        return "energy_transfer"
    if any(k in low for k in ("turbine", "blade", "spin")):
        return "rotate"
    if any(k in low for k in ("wind",)):
        return "flow"
    if any(k in low for k in ("absorb", "uptake", "root")):
        return "absorb"
    return "flow"


def _elements_from_text(text: str, topic: str) -> list[str]:
    """Pick up to 3 syllabus elements named in the text."""
    low = text.lower()
    picked: list[str] = []
    allow = allowed_elements(topic)

    def add(token: str) -> None:
        if token in allow and token not in picked:
            picked.append(token)

    if "sun" in low or "solar" in low:
        add("sun")
    if "cloud" in low:
        add("cloud")
    if "ocean" in low or "sea" in low or "lake" in low:
        add("ocean")
    if "mountain" in low:
        add("mountain")
    if "rain" in low or "water" in low or "vapor" in low or "vapour" in low or "droplet" in low:
        add("molecule_water")
    if "carbon" in low or "co2" in low:
        add("molecule_co2")
    if "oxygen" in low or " o2" in low:
        add("molecule_o2")
    if "leaf" in low or "leafs" in low:
        add("leaf")
    if "plant" in low or "crop" in low:
        add("plant")
    if "root" in low:
        add("root")
    if "sugar" in low or "glucose" in low or "food" in low:
        add("glucose")
    if "wind" in low:
        add("wave")
    if "electric" in low or "power" in low or "energy" in low:
        add("bolt")
    if "hot" in low or "cold" in low or "temperature" in low:
        add("thermometer")
    if "rock" in low:
        add("rock")

    if not picked:
        # Minimal defaults by topic
        defaults = {
            "water_cycle": ["sun", "ocean"],
            "plant_processes": ["sun", "leaf"],
            "solar_energy": ["sun", "bolt"],
            "wind_energy": ["cloud", "bolt"],
            "energy": ["sun", "rock"],
        }
        for d in defaults.get(topic, ["sun", "label"]):
            add(d)
            if len(picked) >= 2:
                break

    return picked[:3]


def chunks_to_visual_plan(
    concept: str,
    chunks: list[list[str]],
    cognitive_load: str,
) -> dict[str, Any]:
    """
    Build a visual plan from Tier-3 bullet chunks (neuro-adaptive pipeline).
    One visual_unit per chunk — deterministic, syllabus-bound.
    """
    load = (cognitive_load or "medium").lower()
    base_topic = detect_syllabus_topic(concept or "")
    units: list[dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        text = " ".join(chunk).strip()
        if not text:
            continue
        topic = detect_syllabus_topic(f"{concept} {text}") or base_topic
        idea = " ".join(text.split()[:10])
        els = _elements_from_text(text, topic)
        action = _infer_action_from_text(text)
        units.append({
            "id": f"nu_{i + 1}",
            "idea": idea[:80],
            "elements": els,
            "action": action,
        })

    if not units:
        return build_rule_only_visual_plan(concept or "science", load)

    merged = validate_and_fix_visual_plan(
        concept or "lesson",
        {"concept": concept or base_topic, "visual_units": units},
        load,
    )
    return merged
