"""
Animation API Schemas – Visual Learning Platform.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ─── Core Actor / Scene / Script ──────────────────────────────────────────────

class Actor(BaseModel):
    """A single visual actor on the animation canvas."""
    id: Optional[str] = None
    type: str
    role: Optional[str] = None          # 'cause' | 'effect' | 'context'
    x: int
    y: int
    animation: str
    color: Optional[str] = None
    size: Optional[int] = None
    count: Optional[int] = 1
    # Type-specific optional fields
    text: Optional[str] = None          # label actors
    fontSize: Optional[int] = None      # label actors
    rays: Optional[bool] = None         # sun actors
    moleculeType: Optional[str] = None  # molecule actors
    angle: Optional[float] = None       # arrow actors
    length: Optional[int] = None        # arrow actors
    thickness: Optional[int] = None     # arrow actors
    extra: Optional[Dict[str, Any]] = None


class AnimationLink(BaseModel):
    """Directed process flow between two actors (rendered as animated dashed line)."""
    type: str = "flow"   # emit | flow | absorb | transform | orbit | attract | repel
    from_actor: str = Field(alias="from")
    to_actor: str = Field(alias="to")
    duration: Optional[int] = None

    class Config:
        populate_by_name = True


class SequenceEvent(BaseModel):
    """
    A timed event within a scene. Events execute one-after-another inside the scene duration.

    Examples:
      { "time": 0,    "action": "appear",  "target": "sun_1" }
      { "time": 800,  "action": "move",    "target": "leaf_1", "to": {"x": 300, "y": 200} }
      { "time": 1600, "action": "glow",    "target": "leaf_1" }
      { "time": 2400, "action": "emit",    "target": "sun_1",  "to_target": "leaf_1" }
    """
    time: int                           # ms offset from scene startTime
    action: str                         # appear | move | glow | pulse | emit | flow | absorb | transform | hide
    target: str                         # actor id this event applies to
    to: Optional[Dict[str, Any]] = None         # destination for 'move': {"x": int, "y": int}
    to_target: Optional[str] = None     # second actor id for emit/flow/absorb
    value: Optional[Any] = None         # optional parameter (scale factor, opacity, etc.)


class Scene(BaseModel):
    """One teaching moment. One idea. One focused visual."""
    id: str
    startTime: int
    duration: int
    learningGoal: Optional[str] = None  # e.g. 'Introduce the sun as energy source'
    focus: Optional[str] = None         # ≤ 6 words: 'Sun emits light'
    text: Optional[str] = None          # 1-sentence caption
    actors: List[Actor] = []
    sequence: Optional[List[SequenceEvent]] = None   # timed event list
    animations: Optional[List[AnimationLink]] = None # process flow links
    environment: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class AnimationScript(BaseModel):
    title: str
    duration: int
    cognitive_level: Optional[str] = None
    cognitive_load: Optional[str] = None
    scenes: List[Scene]


# ─── Standard Generate ────────────────────────────────────────────────────────

CognitiveLoadLevel = Literal["low", "medium", "high"]


class AnimationRequest(BaseModel):
    concept: str
    cognitive_load: CognitiveLoadLevel = Field(
        default="medium",
        description=(
            "Visual complexity level for the learner:\n"
            "  low    = beginner, 1–2 actors/scene, many scenes, slow\n"
            "  medium = intermediate, 2–4 actors/scene, cause-effect chains\n"
            "  high   = advanced, 4–8 actors/scene, fewer scenes, full system view"
        ),
    )


class AnimationResponse(BaseModel):
    script: dict          # JSON animation script
    source: str           # 'prebuilt' | 'cache' | 'generated_comprehensive' | 'generated_hybrid'
    concept: str
    cognitive_load: str   # echo back the level used


# ─── Adaptive (tri-level) Generate ────────────────────────────────────────────

class AdaptiveAnimationRequest(BaseModel):
    concept: str
    levels: List[CognitiveLoadLevel] = Field(
        default=["low", "medium", "high"],
        description="Which cognitive load levels to generate. Defaults to all three.",
    )


class AdaptiveAnimationResponse(BaseModel):
    concept: str
    versions: Dict[str, dict]   # {"low": script, "medium": script, "high": script}
    sources: Dict[str, str]     # {"low": "generated_comprehensive", ...}
    elapsed_seconds: float


# ─── Script Debug & Repair ─────────────────────────────────────────────────

class ScriptDebugRequest(BaseModel):
    script: dict = Field(
        description="The animation script JSON to analyze and repair."
    )
    cognitive_load: CognitiveLoadLevel = Field(
        default="medium",
        description="The cognitive load level the script was generated for.",
    )
    concept: Optional[str] = Field(
        default=None,
        description="Optional concept name to help the AI repair engine understand context.",
    )
    repair: bool = Field(
        default=True,
        description="If True, attempt AI repair after audit. If False, return audit results only.",
    )


class ScriptIssue(BaseModel):
    severity: str           # "error" | "warning" | "suggestion"
    scene_id: Optional[str]
    field: str
    message: str


class ScriptDebugResponse(BaseModel):
    concept: Optional[str]
    cognitive_load: str
    issues_found: List[ScriptIssue]
    severity_summary: Dict[str, int]    # {"error": N, "warning": N, "suggestion": N}
    fix_explanation: str
    repaired_script: dict               # fixed script (or original if repair failed/skipped)
    post_repair_issues: List[ScriptIssue]
    post_repair_summary: Dict[str, int]
    is_valid: bool
    repair_applied: bool


# ─── Neuro-Adaptive (Member 2) ────────────────────────────────────────────────

class NeuroAdaptiveAnimationRequest(BaseModel):
    """
    Request payload for Member 2 – Neuro-Adaptive Visual Engine.

    Typically created from a TransmutedContent document:
    - transmuted_text  -> output.transmuted_text
    - cognitive_state  -> input.cognitive_state
    """
    transmuted_text: str
    cognitive_state: str
    concept: Optional[str] = None
    student_id: Optional[str] = None
    lesson_id: Optional[str] = None
    session_id: Optional[str] = None


class NeuroAdaptiveAnimationResponse(BaseModel):
    script: dict          # JSON animation manifest (AnimationScript shape + meta)
    source: str           # 'neuro_adaptive_rule_based'
    concept: str
    cognitive_state: str
    tier: str
    student_id: Optional[str] = None
    lesson_id: Optional[str] = None
    session_id: Optional[str] = None
