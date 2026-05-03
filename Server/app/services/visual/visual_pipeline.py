"""
Visual Learning Pipeline — Orchestrator

Redesigned flow:
  Input text → concept sniff → visual plan (LLM: ideas + elements + actions ONLY)
            → rule_engine.plan_to_script → AnimationScript

Legacy step_extractor / step_to_visual / script_builder paths are retained as helpers
for other code but are no longer used by run_pipeline().
"""

from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    """Complete output of the visual learning pipeline."""

    # Input metadata
    input_text:       str = ""
    word_count:       int = 0
    concept:          str = ""
    domain:           str = "generic"
    cognitive_load:   str = "medium"

    # Stage outputs (for debugging / transparency)
    steps:            list[str] = field(default_factory=list)
    visual_steps:     list[dict] = field(default_factory=list)

    # Final deliverable
    animation_script: dict = field(default_factory=dict)

    # Pipeline health
    stage_times_ms:   dict[str, float] = field(default_factory=dict)
    warnings:         list[str] = field(default_factory=list)
    success:          bool = False
    error:            Optional[str] = None


# ─── Stage 1: Step Extraction ─────────────────────────────────────────────────

def _stage1_extract_steps(
    text: str,
    max_steps: int,
    use_llm: bool,
) -> tuple[list[str], list[str]]:
    """
    Extract 4–5 simplified steps from raw educational text.

    Returns: (steps, warnings)
    """
    from app.services.nlp.step_extractor import extract_steps

    warnings: list[str] = []
    word_count = len(text.split())

    if word_count < 20:
        warnings.append(f"Text is very short ({word_count} words). Step quality may be low.")
    if word_count > 400:
        warnings.append(f"Text is long ({word_count} words). Trimming to first 350 words.")
        text = " ".join(text.split()[:350])

    steps = extract_steps(
        text,
        max_steps=max_steps,
        use_llm=use_llm,
        add_prefixes=False,   # No "First,/Next," — steps go into visual units
    )

    if not steps:
        warnings.append("Step extraction returned empty list — using fallback.")
        steps = [text[:120].strip()]

    logger.info("[pipeline] Stage 1 complete: %d steps extracted.", len(steps))
    return steps, warnings


# ─── Stage 2: Visual Mapping ──────────────────────────────────────────────────

def _stage2_map_to_visual(
    steps: list[str],
    step_duration_ms: int,
) -> tuple[list[dict], list[str]]:
    """
    Map step strings to VisualStep dicts.

    Returns: (visual_steps, warnings)
    """
    from app.services.visual.step_to_visual import steps_to_visual_sequence

    warnings: list[str] = []
    visual_steps = steps_to_visual_sequence(steps, step_duration_ms=step_duration_ms)

    empty_scenes = [i for i, vs in enumerate(visual_steps) if not vs.get("actors")]
    if empty_scenes:
        warnings.append(
            f"Steps at positions {empty_scenes} produced no actors. "
            "Check WORD_TO_ACTOR coverage for those step words."
        )

    logger.info("[pipeline] Stage 2 complete: %d visual steps mapped.", len(visual_steps))
    return visual_steps, warnings


# ─── Stage 3: Scene Assembly ──────────────────────────────────────────────────

def _stage3_assemble_script(
    visual_steps: list[dict],
    concept: str,
    domain: str,
    cognitive_load: str,
) -> tuple[dict, list[str]]:
    """
    Assemble VisualStep dicts into a full AnimationScript.
    Injects timeline[], animations[], and environment into each scene.

    Returns: (script, warnings)
    """
    from app.services.visual.script_builder import build_script, validate_script_structure

    warnings: list[str] = []

    # Convert VisualStep format → scene format expected by script_builder
    scenes = []
    for vs in visual_steps:
        scene = {
            "id":          vs.get("id", f"step_{len(scenes)+1}"),
            "text":        vs.get("step_text", ""),
            "actors":      _inject_actor_ids_and_timelines(vs.get("actors", [])),
            "animations":  [vs["relationship"]] if vs.get("relationship") else [],
            "environment": _infer_environment(domain),
            "focus":       _derive_focus(vs.get("step_text", "")),
        }
        scenes.append(scene)

    concept_analysis = {"domain": domain, "topic": concept, "cognitive_load": cognitive_load}
    script = build_script(concept.title(), scenes, concept_analysis)
    script["concept"] = concept.lower()
    script["cognitive_level"] = cognitive_load

    if not validate_script_structure(script):
        warnings.append("Script failed validation — startTime values were auto-corrected.")

    logger.info(
        "[pipeline] Stage 3 complete: %d scenes, total %dms.",
        len(script.get("scenes", [])), script.get("duration", 0),
    )
    return script, warnings


def _inject_actor_ids_and_timelines(actors: list[dict]) -> list[dict]:
    """
    Add unique IDs and staggered timeline[] to each actor.
    Timeline staggers appearances: actor[0] at 0ms, actor[1] at 600ms, etc.
    Arrow actors always appear AFTER both their connected actors.
    """
    result = []
    arrow_delay_ms = 1400  # arrows appear after content actors

    # Separate content actors from arrows (arrows go last visually)
    content = [a for a in actors if a.get("type") != "arrow"]
    arrows  = [a for a in actors if a.get("type") == "arrow"]

    stagger_ms = 600  # ms between each content actor appearing

    for idx, actor in enumerate(content + arrows):
        a = dict(actor)
        atype = a.get("type", "actor")

        # Unique ID: type + 1-based index
        a["id"] = f"{atype}_{idx + 1}"

        # Timeline: staggered fade-in
        if atype == "arrow":
            appear_at = arrow_delay_ms
        else:
            appear_at = idx * stagger_ms

        a["timeline"] = [
            {"at": 0,              "alpha": 0},
            {"at": appear_at,      "alpha": 0},
            {"at": appear_at + 500, "alpha": 1, "easing": "easeOut"},
        ]
        result.append(a)

    return result


def _derive_focus(step_text: str) -> str:
    """Derive a ≤6-word focus label from a step string."""
    # Strip common prefixes
    import re
    cleaned = re.sub(r'^(first|next|then|after that|finally)[,\s]+', '', step_text.lower())
    words = cleaned.split()
    focus = " ".join(words[:6]).strip().rstrip(".")
    return focus[0].upper() + focus[1:] if focus else step_text[:40]


def _infer_environment(domain: str) -> str:
    """Map domain to environment hint for background rendering."""
    return {
        "astronomy":    "space",
        "physics":      "default",
        "biology":      "earth",
        "earth_science":"earth",
        "chemistry":    "default",
        "generic":      "default",
    }.get(domain, "default")


# ─── Stage 4: Cognitive Adjustment ───────────────────────────────────────────

def _stage4_adapt(script: dict, cognitive_load: str) -> tuple[dict, list[str]]:
    """
    Adapt the assembled script to the target cognitive load level.
    Returns: (adapted_script, warnings)
    """
    from app.services.visual.cognitive_adapter import adapt_script

    warnings: list[str] = []
    adapted = adapt_script(script, cognitive_load=cognitive_load)

    # Sanity check: ensure we have actors after adaptation
    empty_after = [
        s["id"] for s in adapted.get("scenes", [])
        if not s.get("actors")
    ]
    if empty_after:
        warnings.append(
            f"Scenes {empty_after} have no actors after adaptation. "
            f"Check actor priority weights for '{cognitive_load}' level."
        )

    logger.info(
        "[pipeline] Stage 4 complete: adapted to '%s'. "
        "Scenes: %d, Duration: %dms.",
        cognitive_load,
        len(adapted.get("scenes", [])),
        adapted.get("duration", 0),
    )
    return adapted, warnings


# ─── Stage 5: Final validation + cleanup ──────────────────────────────────────

def _stage5_finalise(script: dict) -> tuple[dict, list[str]]:
    """
    Final cleanup pass:
    - Enforce text length limits
    - Remove actors with invalid positions
    - Ensure every scene has at least one actor
    - Correct total duration
    """
    from app.services.visual.script_builder import validate_script_structure

    warnings: list[str] = []
    out = copy.deepcopy(script)

    for scene in out.get("scenes", []):
        # Clamp text to 18 words max
        text = scene.get("text", "")
        words = text.split()
        if len(words) > 18:
            scene["text"] = " ".join(words[:18]).rstrip(".,;") + "."

        # Remove out-of-bounds actors
        valid_actors = []
        for actor in scene.get("actors", []):
            x = actor.get("x")
            y = actor.get("y")
            if x is None or y is None:
                warnings.append(f"Actor '{actor.get('type')}' in scene '{scene['id']}' missing x/y — removed.")
                continue
            if not (60 <= x <= 740 and 60 <= y <= 540):
                warnings.append(
                    f"Actor '{actor.get('type')}' at ({x},{y}) out of bounds — clamped."
                )
                actor["x"] = max(60, min(int(x), 740))
                actor["y"] = max(60, min(int(y), 540))
            valid_actors.append(actor)
        scene["actors"] = valid_actors

        # Ensure fallback if no valid actors remain
        if not scene["actors"]:
            warnings.append(f"Scene '{scene['id']}' has no valid actors — adding fallback label.")
            scene["actors"] = [{
                "id": "label_fallback",
                "type": "label",
                "x": 400, "y": 300,
                "size": 20,
                "color": "#2563EB",
                "animation": "appear",
                "text": scene.get("focus", "Key concept")[:20],
                "fontSize": 18,
                "timeline": [{"at": 0, "alpha": 0}, {"at": 300, "alpha": 1, "easing": "easeOut"}],
            }]

    # Recompute total duration
    out["duration"] = sum(s.get("duration", 0) for s in out.get("scenes", []))

    validate_script_structure(out)  # auto-corrects startTimes
    logger.info("[pipeline] Stage 5 complete. Final duration: %dms.", out.get("duration", 0))
    return out, warnings


# ─── Domain detection ─────────────────────────────────────────────────────────

def _detect_domain(text: str, concept: str = "") -> str:
    """Quick keyword-based domain detection."""
    combined = (text + " " + concept).lower()
    if any(k in combined for k in ["photosynthesis","cell","leaf","plant","organism","dna","gene","biology"]):
        return "biology"
    if any(k in combined for k in ["water cycle","rock cycle","volcano","earthquake","erosion","sediment","weathering","tectonic"]):
        return "earth_science"
    if any(k in combined for k in ["gravity","force","motion","velocity","acceleration","energy","wave","electricity","magnetism"]):
        return "physics"
    if any(k in combined for k in ["atom","molecule","reaction","bond","element","compound","acid","base","oxidation"]):
        return "chemistry"
    if any(k in combined for k in ["planet","solar","star","galaxy","orbit","moon","comet","asteroid","nebula"]):
        return "astronomy"
    return "generic"


def _detect_concept(text: str, domain: str) -> str:
    """Extract a short concept name from the text."""
    CONCEPT_SIGNALS = {
        "biology":      ["photosynthesis","cell division","respiration","evolution","genetics"],
        "earth_science":["water cycle","rock cycle","erosion","weathering","tectonic plates"],
        "physics":      ["gravity","force","motion","energy","sound","light","magnetism","electricity"],
        "chemistry":    ["atoms","molecules","chemical reaction","bonding","oxidation"],
        "astronomy":    ["solar system","orbit","gravity","stars","planets","galaxy"],
    }
    lower = text.lower()
    for signal in CONCEPT_SIGNALS.get(domain, []):
        if signal in lower:
            return signal.title()
    # Fallback: first 3 significant words
    words = [w for w in text.split() if len(w) > 3][:3]
    return " ".join(words).title() or "Science Concept"


# ─── Step duration calculator ─────────────────────────────────────────────────

def _step_duration_for_level(cognitive_load: str) -> int:
    """Base step duration before cognitive_adapter adjusts it."""
    return {"low": 6000, "medium": 5000, "high": 4000}.get(cognitive_load, 5000)


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def run_pipeline(
    text: str,
    cognitive_load: str = "medium",
    use_llm: bool = False,
    max_steps: int = 5,
) -> PipelineResult:
    """
    Run the Grade 6 visual pipeline: concept → visual plan → rule_engine script.

    Args:
        text:           Student phrase or short passage (concept line works best).
        cognitive_load: low | medium | high (controls units + actor caps in rules).
        use_llm:        If True, Gemini proposes visual_units; if False, syllabus-only plan.
        max_steps:      Unused (kept for API compatibility).
    """
    _ = max_steps
    result = PipelineResult(
        input_text=text,
        word_count=len(text.split()),
        cognitive_load=cognitive_load,
    )

    try:
        from app.services.visual.rule_engine import plan_to_script
        from app.services.visual.visual_planner import build_visual_plan, build_rule_based_visual_plan

        result.domain = _detect_domain(text)
        result.concept = _detect_concept(text, result.domain)

        t0 = time.perf_counter()
        if use_llm:
            visual_plan = build_visual_plan(result.concept, cognitive_load)
        else:
            visual_plan = build_rule_based_visual_plan(result.concept, cognitive_load)
        result.stage_times_ms["1_visual_plan"] = round((time.perf_counter() - t0) * 1000, 1)

        result.steps = [
            str(u.get("idea", ""))
            for u in visual_plan.get("visual_units", [])
            if isinstance(u, dict)
        ]

        t0 = time.perf_counter()
        script = plan_to_script(visual_plan)
        result.stage_times_ms["2_rule_engine"] = round((time.perf_counter() - t0) * 1000, 1)

        result.animation_script = script
        result.success = True

        total_ms = sum(result.stage_times_ms.values())
        logger.info(
            "[pipeline] SUCCESS concept='%s' load='%s' scenes=%d duration=%dms time=%.0fms",
            result.concept, cognitive_load,
            len(script.get("scenes", [])), script.get("duration", 0), total_ms,
        )

    except Exception as e:
        import traceback
        result.error = str(e)
        result.success = False
        logger.error("[pipeline] FAILED: %s\n%s", e, traceback.format_exc())

    return result


def run_pipeline_all_levels(
    text: str,
    use_llm: bool = False,
    max_steps: int = 5,
) -> dict[str, PipelineResult]:
    """
    Run the pipeline for all three cognitive load levels in one call.
    Useful for pre-generating all variants when a lesson is uploaded.

    Returns:
        {
          "low":    PipelineResult,
          "medium": PipelineResult,
          "high":   PipelineResult,
        }
    """
    return {
        level: run_pipeline(text, cognitive_load=level, use_llm=use_llm, max_steps=max_steps)
        for level in ("low", "medium", "high")
    }
