"""
Concept Graph — steps (from LLM) → visual_units + edge list for the rule engine.

LLM only returns { concept, steps[] }. This module is fully deterministic.
"""
from __future__ import annotations

from typing import Any

from app.services.visual.grade6_syllabus import (
    _elements_from_text,
    _infer_action_from_text,
    detect_syllabus_topic,
)


def _truncate_words(s: str, max_words: int = 12) -> str:
    w = s.split()
    return " ".join(w[:max_words]) if w else ""


def build_graph_and_visual_units(
    concept: str,
    steps: list[str],
    cognitive_load: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    load = (cognitive_load or "medium").lower()
    if load not in ("low", "medium", "high"):
        load = "medium"

    topic = detect_syllabus_topic(concept or "")
    clean_steps = [_truncate_words(str(s).strip()) for s in steps if str(s).strip()]
    if not clean_steps:
        clean_steps = [_truncate_words(concept or "Science idea")]

    units: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []

    uidx = 0

    if load == "low":
        # One scene per step — up to two focal elements (simple repetition tier).
        for step in clean_steps:
            els = _elements_from_text(step, topic)[:2]
            action = _infer_action_from_text(step)
            uid = f"u{uidx + 1}"
            units.append({"id": uid, "idea": step, "elements": els or ["label"], "action": action})
            uidx += 1

    else:
        cap = 3 if load == "medium" else 5
        for step in clean_steps:
            els = _elements_from_text(step, topic)[:cap]
            action = _infer_action_from_text(step)
            uid = f"u{uidx + 1}"
            units.append({"id": uid, "idea": step, "elements": els or ["label"], "action": action})
            if len(els) >= 2:
                graph_edges.append({
                    "unit_id": uid,
                    "from_element": els[0],
                    "to_element": els[1],
                    "action": action,
                })
            uidx += 1

        # HIGH: enriched graph — explicit cycle reminder for water cycle
        if load == "high" and topic == "water_cycle" and len(units) >= 2:
            first = units[0].get("elements") or []
            last = units[-1].get("elements") or []
            fe = first[0] if first else "sun"
            le = last[0] if last else "ocean"
            if fe != le:
                uid = f"u{uidx + 1}"
                units.append({
                    "id": uid,
                    "idea": "Water keeps moving in a cycle",
                    "elements": [le, fe],
                    "action": "flow",
                })
                graph_edges.append({
                    "unit_id": uid,
                    "from_element": le,
                    "to_element": fe,
                    "action": "flow",
                    "kind": "cycle_close",
                })

    graph = {
        "topic": topic,
        "cognitive_load": load,
        "edges": graph_edges,
        "units_planned": len(clean_steps),
    }
    return units, graph
