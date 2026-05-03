"""
Visual Planner — LLM performs concept extraction ONLY:

  { "concept": "<short phrase>", "steps": ["...", "..."] }

No actors, animations, coordinates, or UI. The concept graph + rule engine derive visuals.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from app.services.visual.grade6_syllabus import (
    build_rule_only_visual_plan,
    validate_and_fix_visual_plan,
)

logger = logging.getLogger(__name__)


def sniff_domain(concept: str) -> str:
    """Backward-compatible coarse domain for APIs."""
    from app.services.visual.grade6_syllabus import detect_syllabus_topic

    t = detect_syllabus_topic(concept)
    if t == "water_cycle":
        return "earth_science"
    if t in ("plant_processes",):
        return "biology"
    return "physics"


_STRICT_SCHEMA = """
Return ONLY valid JSON (no markdown, no code fences):
{
  "concept": "<2-6 words, one science topic>",
  "visual_units": [
    {
      "idea": "<max 8 words: what the student should notice>",
      "elements": ["<token>", "<token>"],
      "action": "<one verb: evaporation|condensation|precipitation|photosynthesis|flow|emit|absorb|energy_transfer|rotate|appear|grow>"
    }
  ]
}

Allowed element tokens (pick only these spellings):
sun, ocean, cloud, mountain, plant, leaf, root, molecule_water, molecule_co2, molecule_o2,
glucose, bolt, wave, rock, thermometer, arrow, volcano, earth, planet, moon, atom, cell

Rules:
- 4–8 visual_units for MEDIUM/HIGH; for LOW cognitive level still output 5–7 units (server will simplify).
- Each unit = ONE teaching beat; elements lists 1–3 tokens showing what is on screen (no coordinates).
- NO paragraphs, NO scene labels, NO x/y positions, NO animation curve names, NO JSON besides this object.
"""


def _build_planner_prompt(user_text: str, cognitive_load: str) -> str:
    load = cognitive_load.upper()
    load_rules = {
        "low": "Planner breadth: 5–7 units; keep each idea extremely simple.",
        "medium": "6–8 units; each unit advances one link in a process or cycle.",
        "high": "7–9 units; include units that connect earlier and later ideas.",
    }
    return f"""You are a Grade 6 science visual planner. Output a STRUCTURED VISUAL PLAN only.

USER_INPUT: "{user_text}"
COGNITIVE_LEVEL: {load}
{load_rules.get(cognitive_load.lower(), load_rules["medium"])}

{_STRICT_SCHEMA}
"""


def build_visual_plan(concept: str, cognitive_load: str = "medium", domain: Optional[str] = None) -> dict[str, Any]:
    """
    Produces a validated visual_plan (with visual_units + optional concept_graph).
    LLM returns only concept+steps; graph + units are built deterministically.
    """
    _ = domain
    load = (cognitive_load or "medium").lower()
    if load not in ("low", "medium", "high"):
        load = "medium"

    use_llm = os.getenv("VISUAL_PLANNER_USE_LLM", "true").strip().lower() in (
        "1", "true", "yes", "on",
    )

    if not use_llm:
        return build_rule_only_visual_plan(concept, load)

    try:
        from app.services.visual.ai_generator import _generate_text, clean_json_output

        prompt = _build_planner_prompt(concept, load)
        raw = _generate_text(prompt, temperature=0.12, max_tokens=800)
        cleaned = clean_json_output(raw)
        plan = json.loads(cleaned)
        if not isinstance(plan, dict):
            raise ValueError("Plan is not an object")
        merged = {**plan, "concept": plan.get("concept") or concept}
        vu_list = merged.get("visual_units") if isinstance(merged.get("visual_units"), list) else []
        if not merged.get("steps") and vu_list:
            merged["steps"] = [
                str(u.get("idea", "")).strip()
                for u in vu_list
                if isinstance(u, dict) and str(u.get("idea", "")).strip()
            ]
        if not merged.get("steps") and not vu_list:
            merged["steps"] = [str(merged.get("concept") or concept)]
        return validate_and_fix_visual_plan(concept, merged, load)
    except Exception as e:
        logger.warning("[visual_planner] LLM or parse failed (%s); using rule-only plan", e)
        return build_rule_only_visual_plan(concept, load)


def build_rule_based_visual_plan(concept: str, cognitive_load: str = "medium") -> dict[str, Any]:
    """Syllabus fallback plan without calling the model."""
    return build_rule_only_visual_plan(concept, cognitive_load)
