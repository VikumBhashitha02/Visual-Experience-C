"""
Hybrid Generator — legacy name kept for API compatibility.

All generation is now: visual plan (LLM or syllabus) → rule_engine → script.
This module no longer calls secondary LLM scene planners.
"""
import asyncio
import logging
from typing import Any, Optional

from app.services.visual.ai_generator import validate_json_script

logger = logging.getLogger(__name__)


def generate_hybrid_script(concept: str) -> Optional[dict[str, Any]]:
    """
    Deterministic fallback: same pipeline as primary /animation/generate,
    using rule-based plan construction when the model is unavailable.
    """
    try:
        from app.services.visual.rule_engine import visual_plan_to_script

        script = visual_plan_to_script(concept, "medium")
        if script and validate_json_script(script):
            return script
        return None
    except Exception as e:
        logger.exception("[hybrid_generator] Failed for concept=%r: %s", concept, e)
        return None


async def generate_hybrid_script_async(concept: str) -> Optional[dict]:
    """Async wrapper: run sync generate_hybrid_script in thread."""
    return await asyncio.to_thread(generate_hybrid_script, concept)
