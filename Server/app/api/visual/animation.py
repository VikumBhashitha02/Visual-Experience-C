"""
Animation API – Visual Learning Platform.

Endpoints:
  GET  /api/debug/test-generation              — verify Gemini client
  POST /api/animation/generate                 — single cognitive-load-aware script
  POST /api/animation/generate/adaptive        — all three levels in parallel
  POST /api/animation/debug                    — analyze + repair a script
  POST /api/animation/neuro-adaptive           — CTML neuro-adaptive script
  GET  /api/animation/neuro-adaptive/latest    — latest logged script for student
"""
import asyncio
import logging
import time
import traceback
from typing import Dict

from fastapi import APIRouter, HTTPException, Query

from app.schemas.visual.animation import (
    AdaptiveAnimationRequest,
    AdaptiveAnimationResponse,
    AnimationRequest,
    AnimationResponse,
    NeuroAdaptiveAnimationRequest,
    NeuroAdaptiveAnimationResponse,
    ScriptDebugRequest,
    ScriptDebugResponse,
)
from app.services.visual.cache_service import get_cached_script, is_script_complete, save_script
from app.services.visual import ai_generator
from app.services.visual.hybrid_generator import generate_hybrid_script_async
from app.services.visual.prebuilt import get_prebuilt_script
from app.services.visual.script_repair import audit_script, repair_script, _severity_summary
from app.services.visual.neuro_adaptive_engine import (
    generate_neuro_adaptive_script,
    log_neuro_adaptive_script,
)
from app.models.visual.neuro_adaptive import NeuroAdaptiveVisualScript
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Two-Stage Pipeline Endpoint ─────────────────────────────────────────────

@router.post("/animation/generate/plan")
async def generate_from_visual_plan(
    request: AnimationRequest,
    bypass_cache: bool = Query(False, description="Skip cache"),
):
    """
    NEW: Two-stage cognitive-adaptive pipeline.

    Stage 1 — LLM Visual Planner:
      Generates a concept-level visual_plan (elements + actions, NO positions/sizes).

    Stage 2 — Rule-Based Engine:
      Converts the visual_plan to a fully-specified animation script deterministically.
      Assigns positions, sizes, colors, animations, and timing based on cognitive level.

    Guarantees LOW / MEDIUM / HIGH produce structurally different outputs:
      LOW    → 5–7 scenes, 1 actor each, slow, isolated
      MEDIUM → 4–6 scenes, 2–3 actors, cause→effect arrows
      HIGH   → 3–4 scenes, 4–6 actors, parallel processes
    """
    concept = (request.concept or "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")

    cognitive_load = (request.cognitive_load or "medium").lower()
    if cognitive_load not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="cognitive_load must be low|medium|high")

    t_start = time.monotonic()
    try:
        from app.services.visual.visual_planner import build_visual_plan, sniff_domain
        from app.services.visual.rule_engine import plan_to_script

        domain = sniff_domain(concept)
        visual_plan = await asyncio.to_thread(build_visual_plan, concept, cognitive_load, domain)
        script = plan_to_script(visual_plan)
        script["cognitive_load"] = cognitive_load

        elapsed = time.monotonic() - t_start
        logger.info("[plan-pipeline] concept=%r load=%s domain=%s elapsed=%.2fs",
                    concept, cognitive_load, domain, elapsed)

        return {
            "script": script,
            "visual_plan": visual_plan,
            "source": "new_pipeline",
            "concept": concept.lower(),
            "cognitive_load": cognitive_load,
            "domain": domain,
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        logger.exception("[plan-pipeline] Error for concept=%r", concept)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


# ─── Debug / Health ───────────────────────────────────────────────────────────

@router.get("/debug/test-generation")
async def test_generation():
    """Debug: verify Gemini client, model, and API key."""
    try:
        client = ai_generator.get_client()
        model = ai_generator._get_model_name()
        api_key_set = bool(ai_generator._get_api_key())
        return {
            "status": "ok",
            "client_initialized": True,
            "provider": "gemini",
            "model": model,
            "api_key_set": api_key_set,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_set": bool(ai_generator._get_api_key()),
            "traceback": traceback.format_exc(),
        }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _cache_key(concept_key: str, cognitive_load: str) -> str:
    """Cache key is scoped by concept + cognitive_load so each level is stored independently."""
    return f"{concept_key}::{cognitive_load}"


async def _generate_one(concept: str, cognitive_load: str) -> tuple[dict | None, str]:
    """
    Visual plan (LLM → syllabus-bound JSON) + rule_engine → animation script.
    No direct LLM animation-script generation. Fallbacks are rule-only + hybrid helper.
    """
    try:
        from app.services.visual.rule_engine import visual_plan_to_script

        script = await asyncio.to_thread(visual_plan_to_script, concept, cognitive_load)
        if script and is_script_complete(script) and ai_generator.validate_json_script(script):
            logger.info("[generate_one] Pipeline OK for '%s' [%s]", concept, cognitive_load)
            return script, "new_pipeline"
    except Exception as e:
        logger.warning("[generate_one] Primary pipeline failed (%s)", e)

    try:
        from app.services.visual.rule_engine import plan_to_script
        from app.services.visual.visual_planner import build_rule_based_visual_plan

        def _rule_only() -> dict:
            plan = build_rule_based_visual_plan(concept, cognitive_load)
            return plan_to_script(plan)

        script = await asyncio.to_thread(_rule_only)
        if script and is_script_complete(script) and ai_generator.validate_json_script(script):
            return script, "rule_only"
    except Exception as e:
        logger.warning("[generate_one] Rule-only fallback failed (%s)", e)

    script = await generate_hybrid_script_async(concept)
    if script and is_script_complete(script):
        return script, "generated_hybrid"

    return None, "failed"


def _generate_with_forced_load(concept: str, cognitive_load: str) -> dict | None:
    """
    Generate a script with a FORCED cognitive_load level (visual plan + rule engine only).
    """
    try:
        from app.services.visual.rule_engine import visual_plan_to_script

        script = visual_plan_to_script(concept, cognitive_load)
        if script and ai_generator.validate_json_script(script):
            script["cognitive_load"] = cognitive_load
            logger.info("[adaptive] Pipeline OK for '%s' [%s]", concept, cognitive_load)
            return script
    except Exception as e:
        logger.warning("[adaptive] Primary pipeline failed (%s)", e)

    try:
        from app.services.visual.rule_engine import plan_to_script
        from app.services.visual.visual_planner import build_rule_based_visual_plan

        plan = build_rule_based_visual_plan(concept, cognitive_load)
        script = plan_to_script(plan)
        if script and ai_generator.validate_json_script(script):
            script["cognitive_load"] = cognitive_load
            return script
    except Exception as e:
        logger.error("[adaptive] Rule-only fallback error: %s", e)
    return None


# ─── Single-level Generate ────────────────────────────────────────────────────

@router.post("/animation/generate", response_model=AnimationResponse)
async def generate_animation(
    request: AnimationRequest,
    bypass_cache: bool = Query(False, description="Skip cache and always regenerate"),
):
    """
    Generate or retrieve an animation script adapted to cognitive load.

    Pipeline:
      1. Prebuilt scripts for curated topics
      2. Cache (concept + cognitive_load)
      3. Visual plan (optional Gemini) → rule_engine — deterministic animation JSON
      4. Hybrid helper — syllabus-only rule_engine path
    """
    concept = (request.concept or "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")

    cognitive_load = (request.cognitive_load or "medium").lower()
    if cognitive_load not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="cognitive_load must be 'low', 'medium', or 'high'")

    concept_key = concept.lower()
    cache_key = _cache_key(concept_key, cognitive_load)
    t_start = time.monotonic()

    try:
        # 1. Prebuilt
        prebuilt = get_prebuilt_script(concept)
        if prebuilt is not None:
            logger.info("[animation] concept=%r load=%s source=prebuilt", concept_key, cognitive_load)
            return AnimationResponse(
                script=prebuilt, source="prebuilt",
                concept=concept_key, cognitive_load=cognitive_load,
            )

        # 2. Cache (per-level)
        if not bypass_cache:
            cached = await get_cached_script(cache_key)
            if cached:
                logger.info("[animation] concept=%r load=%s source=cache elapsed=%.2fs",
                    concept_key, cognitive_load, time.monotonic() - t_start)
                return AnimationResponse(
                    script=cached["script"], source=cached["source"],
                    concept=concept_key, cognitive_load=cognitive_load,
                )

        # 3 & 4. Generate
        script, source = await _generate_one(concept, cognitive_load)
        if script:
            await save_script(cache_key, script, source)
            logger.info("[animation] concept=%r load=%s source=%s elapsed=%.2fs",
                concept_key, cognitive_load, source, time.monotonic() - t_start)
            return AnimationResponse(
                script=script, source=source,
                concept=concept_key, cognitive_load=cognitive_load,
            )

        logger.error("[animation] ALL METHODS FAILED concept=%r load=%s", concept_key, cognitive_load)
        raise HTTPException(status_code=500, detail="Failed to generate animation script.")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[animation] Unhandled error for concept=%r load=%s", concept_key, cognitive_load)
        raise HTTPException(status_code=500, detail=f"Error generating animation: {str(e)}")


# ─── Tri-level Adaptive Generate ──────────────────────────────────────────────

@router.post("/animation/generate/adaptive", response_model=AdaptiveAnimationResponse)
async def generate_adaptive_animation(
    request: AdaptiveAnimationRequest,
    bypass_cache: bool = Query(False, description="Skip cache and always regenerate all levels"),
):
    """
    Generate COMPLETELY DIFFERENT animation scripts for each cognitive load level in parallel.

      LOW    — 7–9 scenes, 1–2 actors/scene, isolated single-object focus, slow
      MEDIUM — 5–7 scenes, 2–4 actors/scene, cause-effect chains, moderate
      HIGH   — 3–5 scenes, 4–8 actors/scene, full system view, parallel processes

    Each level is cached independently (concept + level as cache key).
    """
    concept = (request.concept or "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")

    levels = list({lvl.lower() for lvl in (request.levels or ["low", "medium", "high"])})
    invalid = [l for l in levels if l not in ("low", "medium", "high")]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid levels: {invalid}. Must be low/medium/high.")

    concept_key = concept.lower()
    t_start = time.monotonic()

    async def _get_or_generate(level: str) -> tuple[str, dict | None, str]:
        cache_key = _cache_key(concept_key, level)

        # Prebuilt only for medium (low/high need proper adaptive generation)
        prebuilt = get_prebuilt_script(concept)
        if prebuilt is not None and level == "medium":
            return level, prebuilt, "prebuilt"

        # Cache
        if not bypass_cache:
            cached = await get_cached_script(cache_key)
            if cached:
                logger.info("[adaptive] concept=%r level=%s source=cache", concept_key, level)
                return level, cached["script"], cached["source"]

        # Force the requested cognitive_load (bypass auto-detection)
        script = await asyncio.to_thread(_generate_with_forced_load, concept, level)
        if script and is_script_complete(script):
            await save_script(cache_key, script, "generated_adaptive")
            logger.info("[adaptive] concept=%r level=%s source=generated_adaptive", concept_key, level)
            return level, script, "generated_adaptive"

        # Hybrid fallback
        hybrid = await generate_hybrid_script_async(concept)
        if hybrid and is_script_complete(hybrid):
            await save_script(cache_key, hybrid, "generated_hybrid")
            logger.info("[adaptive] concept=%r level=%s source=generated_hybrid", concept_key, level)
            return level, hybrid, "generated_hybrid"

        logger.warning("[adaptive] concept=%r level=%s FAILED", concept_key, level)
        return level, None, "failed"

    try:
        results = await asyncio.gather(*[_get_or_generate(l) for l in levels])

        versions: Dict[str, dict] = {}
        sources: Dict[str, str] = {}
        for level, script, source in results:
            if script:
                versions[level] = script
                sources[level] = source

        if not versions:
            raise HTTPException(status_code=500, detail="All cognitive load levels failed to generate.")

        elapsed = time.monotonic() - t_start
        logger.info("[adaptive] concept=%r levels=%s elapsed=%.2fs", concept_key, list(versions.keys()), elapsed)
        return AdaptiveAnimationResponse(
            concept=concept_key, versions=versions, sources=sources,
            elapsed_seconds=round(elapsed, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[adaptive] Unhandled error for concept=%r", concept_key)
        raise HTTPException(status_code=500, detail=f"Error generating adaptive animation: {str(e)}")


# ─── Script Debug & Repair ────────────────────────────────────────────────────

@router.post("/animation/debug", response_model=ScriptDebugResponse)
async def debug_animation_script(request: ScriptDebugRequest):
    """
    Script Analysis & Repair Pipeline.

    Phase 1 — Rule-based Audit (instant, no AI call):
      18 checks including: missing fields, invalid types/animations, out-of-bounds positions,
      static scenes, cognitive load violations, timing errors, duplicate IDs.

    Phase 2 — AI Repair (Gemini, only if repair=True):
      Sends audit report + original script to Gemini for targeted redesign.
      Re-audits the repaired output to confirm all errors resolved.

    Returns full issue list, severity summary, fix explanation, and repaired script.
    """
    cognitive_load = (request.cognitive_load or "medium").lower()
    concept = (request.concept or "").strip() or None
    t_start = time.monotonic()

    try:
        if request.repair:
            result = await asyncio.to_thread(
                repair_script, request.script, cognitive_load, concept,
            )
        else:
            issues = audit_script(request.script, cognitive_load)
            summary = _severity_summary(issues)
            result = {
                "issues_found": issues,
                "severity_summary": summary,
                "fix_explanation": "Audit-only mode — no repair attempted.",
                "repaired_script": request.script,
                "post_repair_issues": [],
                "post_repair_summary": {"error": 0, "warning": 0, "suggestion": 0},
                "is_valid": summary["error"] == 0,
                "repair_applied": False,
            }

        elapsed = time.monotonic() - t_start
        logger.info("[debug] load=%s errors=%d repaired=%s elapsed=%.2fs",
            cognitive_load, result["severity_summary"]["error"],
            result["repair_applied"], elapsed)

        return ScriptDebugResponse(
            concept=concept,
            cognitive_load=cognitive_load,
            issues_found=result["issues_found"],
            severity_summary=result["severity_summary"],
            fix_explanation=result["fix_explanation"],
            repaired_script=result["repaired_script"],
            post_repair_issues=result["post_repair_issues"],
            post_repair_summary=result["post_repair_summary"],
            is_valid=result["is_valid"],
            repair_applied=result["repair_applied"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[debug] Unhandled error")
        raise HTTPException(status_code=500, detail=f"Error during script analysis: {str(e)}")


# ─── Neuro-Adaptive (Member 2) ────────────────────────────────────────────────

@router.post(
    "/animation/neuro-adaptive",
    response_model=NeuroAdaptiveAnimationResponse,
    summary="Generate neuro-adaptive animation script from Tier 3 bullets + cognitive state",
)
async def generate_neuro_adaptive_animation(request: NeuroAdaptiveAnimationRequest):
    """
    Member 2 – Neuro-Adaptive Visual Engine.
    Consumes transmuted_text + cognitive_state (OVERLOAD|OPTIMAL|LOW_LOAD).
    Returns CTML-principle-guided animation script.
    """
    transmuted_text = (request.transmuted_text or "").strip()
    if not transmuted_text:
        raise HTTPException(status_code=400, detail="transmuted_text is required")

    cognitive_state = (request.cognitive_state or "").strip()
    if not cognitive_state:
        raise HTTPException(status_code=400, detail="cognitive_state is required")

    concept = (request.concept or "").strip() or "Adaptive Visual Explanation"

    try:
        script = generate_neuro_adaptive_script(
            transmuted_text=transmuted_text,
            cognitive_state=cognitive_state,
            concept=concept,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500,
            detail=f"Error generating neuro-adaptive animation: {str(e)}")

    from app.services.visual.neuro_adaptive_engine import _map_state_to_tier, _normalize_state
    state_norm = _normalize_state(cognitive_state)
    tier = _map_state_to_tier(state_norm)

    if request.lesson_id or request.student_id or request.session_id:
        await log_neuro_adaptive_script(
            script, cognitive_state=state_norm, tier=tier, concept=concept,
            lesson_id=request.lesson_id, student_id=request.student_id,
            session_id=request.session_id,
        )

    return NeuroAdaptiveAnimationResponse(
        script=script, source="neuro_adaptive_rule_based", concept=concept,
        cognitive_state=state_norm, tier=tier,
        student_id=request.student_id, lesson_id=request.lesson_id,
        session_id=request.session_id,
    )


# ─── Neuro-Adaptive Latest ────────────────────────────────────────────────────

@router.get(
    "/animation/neuro-adaptive/latest",
    response_model=NeuroAdaptiveAnimationResponse,
    summary="Fetch latest neuro-adaptive visual script for a student (optional session)",
)
async def get_latest_neuro_adaptive_animation(
    student_id: str,
    session_id: str | None = None,
):
    try:
        student_obj_id = PydanticObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student_id")

    filters = [NeuroAdaptiveVisualScript.student_id == student_obj_id]
    if session_id is not None:
        filters.append(NeuroAdaptiveVisualScript.session_id == session_id)

    doc = await NeuroAdaptiveVisualScript.find(*filters).sort("-created_at").first_or_none()
    if not doc:
        raise HTTPException(status_code=404,
            detail="No neuro-adaptive visual script found for this student/session")

    return NeuroAdaptiveAnimationResponse(
        script=doc.script, source="neuro_adaptive_logged",
        concept=doc.concept, cognitive_state=doc.cognitive_state, tier=doc.tier,
        student_id=str(doc.student_id) if doc.student_id else None,
        lesson_id=str(doc.lesson_id) if doc.lesson_id else None,
        session_id=doc.session_id,
    )
