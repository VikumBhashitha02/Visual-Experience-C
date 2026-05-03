"""
Neuro-Adaptive Visual Engine (Member 2)

Transforms Tier 3 transmuted text + cognitive state into an animation script JSON
that the React Native canvas/Lottie layer can render live.

Research framing:
- OVERLOAD  -> Coherence + Signaling, low visual salience
- OPTIMAL   -> Segmenting + Signaling, medium salience
- LOW_LOAD  -> Personalization + Generative processing, high salience

This engine does NOT generate video files. It produces a structured JSON manifest
matching the existing AnimationScript shape:
{
  "title": str,
  "duration": int,
  "scenes": [
    {
      "id": str,
      "startTime": int,
      "duration": int,
      "text": str,
      "actors": [...],
      "environment": str,
      "meta": {
        "cognitiveState": "OVERLOAD" | "OPTIMAL" | "LOW_LOAD",
        "tier": "Tier 1/2/3 ...",
        "ctmlPrinciples": [...],
        "salienceLevel": "low" | "medium" | "high"
      }
    }
  ]
}
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from beanie import PydanticObjectId

from app.models.visual.neuro_adaptive import NeuroAdaptiveVisualScript
from app.services.visual.grade6_syllabus import chunks_to_visual_plan
from app.services.visual.rule_engine import plan_to_script
from app.services.cognitive_load.constants import (
    normalize_wire_state,
    get_ctml_principles,
    get_salience_level,
    get_environment,
)


def _normalize_state(cognitive_state: str) -> str:
    """Normalize cognitive state string to canonical wire format."""
    return normalize_wire_state(cognitive_state)


def _map_state_to_tier(state: str) -> str:
    if state == "OVERLOAD":
        return "Tier 3 - Cognitive Offloading"
    if state == "LOW_LOAD":
        return "Tier 1 - Enrichment and Elaboration"
    return "Tier 2 - Moderate Simplification"


def _parse_bullets(transmuted_text: str) -> List[str]:
    """
    Parse Tier‑3 style bullet list into clean bullet strings.
    Accepts bullets that start with '*', '-', or '•'.
    """
    bullets: List[str] = []
    for raw_line in (transmuted_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line[0] in {"*", "-", "•"}:
            line = line[1:].strip()
        if line:
            bullets.append(line)
    return bullets


def _chunk_bullets_for_state(bullets: List[str], state: str) -> List[List[str]]:
    """
    Apply CTML‑aware chunking strategy:
    - OVERLOAD: 1 bullet per scene (maximal chunking, strong temporal contiguity)
    - OPTIMAL:  2 bullets per scene (segmenting)
    - LOW_LOAD: 3 bullets per scene (slightly richer scenes to foster generative load)
    """
    if not bullets:
        return []
    if state == "OVERLOAD":
        size = 1
    elif state == "LOW_LOAD":
        size = 3
    else:
        size = 2
    return [bullets[i : i + size] for i in range(0, len(bullets), size)]


def _scene_meta(state: str) -> Dict[str, Any]:
    """Return CTML‑oriented meta block for a scene."""
    return {
        "cognitiveState": state,
        "tier": _map_state_to_tier(state),
        "ctmlPrinciples": get_ctml_principles(state),
        "salienceLevel": get_salience_level(state),
    }


def _environment_for_state(state: str) -> str:
    """Return background environment hint for cognitive state."""
    return get_environment(state)


def _cognitive_state_to_load(state: str) -> str:
    """
    Map neuro wire state to animation pipeline load.
    OVERLOAD  — simplify (isolated scenes, 1–2 actors)  → low
    OPTIMAL   — balanced                                → medium
    LOW_LOAD  — student can take richer visuals         → high
    """
    if state == "OVERLOAD":
        return "low"
    if state == "LOW_LOAD":
        return "high"
    return "medium"


def _apply_neuro_metadata(script: Dict[str, Any], state: str) -> None:
    """Attach CTML meta + environment onto rule-engine scenes (in-place)."""
    for scene in script.get("scenes") or []:
        if isinstance(scene, dict):
            scene["meta"] = _scene_meta(state)
            scene["environment"] = _environment_for_state(state)


def generate_neuro_adaptive_script(
    transmuted_text: str,
    cognitive_state: str,
    *,
    concept: str | None = None,
) -> Dict[str, Any]:
    """
    Public entry point for Member 2.

    Inputs:
    - transmuted_text: Tier‑3 cognitive offloading bullets from Member 1
    - cognitive_state: "OVERLOAD" | "OPTIMAL" | "LOW_LOAD"

    Output: JSON animation script ready to be sent to the mobile app.
    """
    state = _normalize_state(cognitive_state)
    bullets = _parse_bullets(transmuted_text)
    if not bullets:
        # Fallback: treat full text as a single "idea".
        bullets = [transmuted_text.strip() or "Explanation"]

    chunks = _chunk_bullets_for_state(bullets, state)
    load = _cognitive_state_to_load(state)
    title = (concept or "Adaptive Visual Explanation").strip() or "Adaptive Visual Explanation"

    visual_plan = chunks_to_visual_plan(title, chunks, load)
    script = plan_to_script(visual_plan)
    script["title"] = title
    script["concept"] = title
    _apply_neuro_metadata(script, state)

    return script


async def log_neuro_adaptive_script(
    script: Dict[str, Any],
    *,
    cognitive_state: str,
    tier: str,
    concept: str,
    lesson_id: Optional[str] = None,
    student_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Persist a neuro-adaptive visual script for later retrieval by the frontend.
    """
    lesson_obj_id: Optional[PydanticObjectId] = None
    student_obj_id: Optional[PydanticObjectId] = None
    if lesson_id:
        try:
            lesson_obj_id = PydanticObjectId(lesson_id)
        except Exception:
            lesson_obj_id = None
    if student_id:
        try:
            student_obj_id = PydanticObjectId(student_id)
        except Exception:
            student_obj_id = None

    doc = NeuroAdaptiveVisualScript(
        lesson_id=lesson_obj_id,
        student_id=student_obj_id,
        session_id=session_id,
        concept=concept,
        cognitive_state=cognitive_state,
        tier=tier,
        script=script,
    )
    await doc.insert()

