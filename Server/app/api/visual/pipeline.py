"""
API endpoint: POST /api/visual/pipeline
Thin HTTP layer over visual_pipeline.run_pipeline().
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.visual.visual_pipeline import run_pipeline, run_pipeline_all_levels

router = APIRouter()


class PipelineRequest(BaseModel):
    text:           str   = Field(..., min_length=30, max_length=2000,
                                  description="Educational text (100–350 words recommended)")
    cognitive_load: str   = Field("medium", pattern="^(low|medium|high)$")
    use_llm:        bool  = Field(False, description="Use Gemini for richer step extraction")
    max_steps:      int   = Field(5, ge=3, le=6)
    all_levels:     bool  = Field(False, description="Generate LOW/MEDIUM/HIGH variants at once")


@router.post("/visual/pipeline")
async def visual_pipeline(req: PipelineRequest):
    """
    Full visual learning pipeline.

    Input:  Raw educational text + cognitive load level.
    Output: AnimationScript JSON ready for the React Native renderer.

    Pipeline:
      text → step_extractor → step_to_visual → script_builder
           → cognitive_adapter → validation → AnimationScript
    """
    if req.all_levels:
        variants = run_pipeline_all_levels(
            req.text, use_llm=req.use_llm, max_steps=req.max_steps
        )
        return {
            level: {
                "success":          r.success,
                "concept":          r.concept,
                "domain":           r.domain,
                "steps":            r.steps,
                "animation_script": r.animation_script,
                "warnings":         r.warnings,
                "stage_times_ms":   r.stage_times_ms,
                "error":            r.error,
            }
            for level, r in variants.items()
        }

    result = run_pipeline(
        req.text,
        cognitive_load=req.cognitive_load,
        use_llm=req.use_llm,
        max_steps=req.max_steps,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Pipeline failed")

    return {
        "success":          result.success,
        "concept":          result.concept,
        "domain":           result.domain,
        "steps":            result.steps,
        "animation_script": result.animation_script,
        "warnings":         result.warnings,
        "stage_times_ms":   result.stage_times_ms,
    }
