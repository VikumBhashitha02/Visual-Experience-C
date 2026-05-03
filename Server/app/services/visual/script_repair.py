"""
Script Analysis & Repair Engine
================================
Rule-based auditor + Gemini-powered redesign pipeline.

The auditor runs deterministically (fast, no API call) and catches:
  - Missing required fields
  - Invalid actor types / animations
  - Static scenes (all actors idle)
  - Cognitive load structure violations
  - Scenes without cause→effect
  - Out-of-bounds positions
  - Duplicate scene IDs
  - Incorrect timing (startTime not cumulative, duration mismatch)

The AI repair engine sends the audit report + original script to Gemini
with a strict educational animation redesign prompt.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

VALID_ACTOR_TYPES = {
    "planet", "earth", "moon", "star", "sun", "asteroid", "comet",
    "cloud", "mountain", "ocean", "volcano", "rock",
    "animal", "cell", "bacteria", "leaf", "root", "plant",
    "molecule", "atom", "electron", "proton", "neutron", "glucose",
    "arrow", "label", "line", "graph", "number", "bolt", "thermometer", "wave",
}

VALID_ANIMATIONS = {
    "appear", "idle", "moveUp", "moveDown", "floatIn", "floatOut",
    "glow", "shine", "bubbleUp", "rotate", "pulse", "wave",
    "sway", "grow", "absorb", "orbit", "spin", "vibrate", "fall",
}

STATIC_ANIMATIONS = {"idle", "appear"}   # animations that imply no meaningful motion

# Cognitive load structural constraints
_CL_RULES = {
    "low": {
        "min_scenes": 5, "max_scenes": 10,
        "max_actors_per_scene": 2,
        "arrow_allowed": False,
        "formula_allowed": False,
    },
    "medium": {
        "min_scenes": 4, "max_scenes": 8,
        "max_actors_per_scene": 4,
        "arrow_allowed": True,
        "formula_allowed": False,   # summary scene only — checked loosely
    },
    "high": {
        "min_scenes": 2, "max_scenes": 6,
        "max_actors_per_scene": 99,  # no upper limit
        "min_actors_per_scene": 4,
        "arrow_allowed": True,
        "formula_allowed": True,
    },
}

CANVAS_X = (60, 740)
CANVAS_Y = (60, 540)


# ─── Issue Dataclass ──────────────────────────────────────────────────────────

class Issue:
    def __init__(self, severity: str, scene_id: str | None, field: str, message: str):
        self.severity = severity   # "error" | "warning" | "suggestion"
        self.scene_id = scene_id
        self.field = field
        self.message = message

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "scene_id": self.scene_id,
            "field": self.field,
            "message": self.message,
        }


# ─── Rule-Based Auditor ───────────────────────────────────────────────────────

def audit_script(script: Any, cognitive_load: str = "medium") -> list[dict]:
    """
    Run full rule-based audit on a script dict.
    Returns list of issue dicts sorted by severity (errors first).
    """
    issues: list[Issue] = []
    cl = cognitive_load.lower()
    rules = _CL_RULES.get(cl, _CL_RULES["medium"])

    if not isinstance(script, dict):
        return [Issue("error", None, "root", "Script must be a JSON object.").to_dict()]

    # ── Top-level structure ───────────────────────────────────────────────────
    for field in ("title", "duration", "scenes"):
        if field not in script:
            issues.append(Issue("error", None, field, f"Missing required top-level field: '{field}'"))

    if "scenes" not in script:
        return [i.to_dict() for i in issues]

    scenes = script.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) == 0:
        issues.append(Issue("error", None, "scenes", "scenes must be a non-empty list"))
        return [i.to_dict() for i in issues]

    # ── Scene count structural check ──────────────────────────────────────────
    n = len(scenes)
    if n < rules["min_scenes"]:
        issues.append(Issue(
            "error", None, "scene_count",
            f"[{cl.upper()}] Too few scenes: got {n}, need at least {rules['min_scenes']}. "
            f"{cl.upper()} load requires more scenes for step-by-step progressive disclosure."
        ))
    if n > rules["max_scenes"]:
        issues.append(Issue(
            "warning", None, "scene_count",
            f"[{cl.upper()}] Too many scenes: got {n}, max recommended is {rules['max_scenes']}."
        ))

    # ── Per-scene audit ───────────────────────────────────────────────────────
    seen_ids: set[str] = set()
    expected_start = 0

    for idx, scene in enumerate(scenes):
        sid = scene.get("id", f"scene_{idx}")

        if not isinstance(scene, dict):
            issues.append(Issue("error", sid, "scene", f"Scene {idx} is not an object"))
            continue

        # Required scene fields
        for f in ("id", "startTime", "duration", "text", "actors"):
            if f not in scene:
                issues.append(Issue("error", sid, f, f"Scene '{sid}' missing required field: '{f}'"))

        # Duplicate IDs
        raw_id = scene.get("id", "")
        if raw_id in seen_ids:
            issues.append(Issue("error", sid, "id", f"Duplicate scene id: '{raw_id}'"))
        seen_ids.add(raw_id)

        # Timing: cumulative startTime
        actual_start = scene.get("startTime", -1)
        if actual_start != expected_start:
            issues.append(Issue(
                "error", sid, "startTime",
                f"Scene '{sid}' startTime={actual_start}, expected {expected_start} "
                f"(cumulative sum of previous durations). Timing will break frontend sync."
            ))
        expected_start = actual_start + scene.get("duration", 0)

        # Duration sanity
        dur = scene.get("duration", 0)
        if dur < 2000:
            issues.append(Issue("warning", sid, "duration",
                f"Scene '{sid}' duration={dur}ms is very short (< 2s). Students won't be able to read it."))
        if dur > 12000:
            issues.append(Issue("warning", sid, "duration",
                f"Scene '{sid}' duration={dur}ms is very long (> 12s). Consider splitting."))

        # Empty text
        text = scene.get("text", "").strip()
        if not text:
            issues.append(Issue("error", sid, "text", f"Scene '{sid}' has empty narration text."))
        elif len(text) < 10:
            issues.append(Issue("warning", sid, "text",
                f"Scene '{sid}' text is very short ({len(text)} chars). May not explain the concept."))

        actors = scene.get("actors", [])
        if not isinstance(actors, list) or len(actors) == 0:
            issues.append(Issue("error", sid, "actors", f"Scene '{sid}' has no actors."))
            continue

        # Actor count structural check
        n_actors = len(actors)
        max_a = rules.get("max_actors_per_scene", 99)
        min_a = rules.get("min_actors_per_scene", 0)
        if n_actors > max_a:
            issues.append(Issue(
                "error", sid, "actors",
                f"[{cl.upper()}] Scene '{sid}' has {n_actors} actors, max allowed is {max_a}. "
                f"Too many actors causes cognitive overload for {cl.upper()} learners."
            ))
        if n_actors < min_a:
            issues.append(Issue(
                "error", sid, "actors",
                f"[{cl.upper()}] Scene '{sid}' only has {n_actors} actors, minimum is {min_a}. "
                f"HIGH load scenes must show the full system simultaneously."
            ))

        # Static scene check
        animations_used = [a.get("animation", "idle") for a in actors if isinstance(a, dict)]
        all_static = all(anim in STATIC_ANIMATIONS for anim in animations_used)
        if all_static and n_actors > 0:
            issues.append(Issue(
                "warning", sid, "animations",
                f"Scene '{sid}' is STATIC — all actors use only idle/appear. "
                f"No motion = no teaching. Add glow, pulse, moveDown, bubbleUp, etc."
            ))

        # No cause→effect check (single actor scenes without meaningful animation)
        has_arrow = any(a.get("type") == "arrow" for a in actors if isinstance(a, dict))
        if n_actors == 1 and not has_arrow and cl in ("medium", "high"):
            if animations_used and animations_used[0] in STATIC_ANIMATIONS:
                issues.append(Issue(
                    "suggestion", sid, "actors",
                    f"Scene '{sid}' has one static actor. [{cl.upper()}] level must show cause→effect. "
                    f"Add at least one more actor or an arrow."
                ))

        # Arrow structural checks
        if not rules["arrow_allowed"]:
            if has_arrow:
                issues.append(Issue(
                    "error", sid, "actors",
                    f"Scene '{sid}' uses arrow actors but [{cl.upper()}] level FORBIDS arrows — "
                    f"they add visual complexity that overwhelms beginner learners."
                ))
        elif cl == "high" and not has_arrow and idx < len(scenes) - 1:
            issues.append(Issue(
                "suggestion", sid, "actors",
                f"[HIGH] Scene '{sid}' has no arrows. HIGH level must show causal network with multiple arrows."
            ))

        # Per-actor validation
        for ai, actor in enumerate(actors):
            if not isinstance(actor, dict):
                issues.append(Issue("error", sid, f"actors[{ai}]", "Actor must be an object"))
                continue

            atype = actor.get("type", "")
            if not atype:
                issues.append(Issue("error", sid, f"actors[{ai}].type", "Actor missing 'type'"))
            elif atype not in VALID_ACTOR_TYPES:
                issues.append(Issue(
                    "error", sid, f"actors[{ai}].type",
                    f"Invalid actor type: '{atype}'. Must be one of the valid types. "
                    f"Frontend cannot render unknown types."
                ))

            # Position bounds
            x = actor.get("x")
            y = actor.get("y")
            if x is None:
                issues.append(Issue("error", sid, f"actors[{ai}].x", "Actor missing 'x' position"))
            elif not (CANVAS_X[0] <= x <= CANVAS_X[1]):
                issues.append(Issue(
                    "error", sid, f"actors[{ai}].x",
                    f"Actor x={x} out of bounds ({CANVAS_X[0]}–{CANVAS_X[1]}). Will render off-screen."
                ))
            if y is None:
                issues.append(Issue("error", sid, f"actors[{ai}].y", "Actor missing 'y' position"))
            elif not (CANVAS_Y[0] <= y <= CANVAS_Y[1]):
                issues.append(Issue(
                    "error", sid, f"actors[{ai}].y",
                    f"Actor y={y} out of bounds ({CANVAS_Y[0]}–{CANVAS_Y[1]}). Will render off-screen."
                ))

            # Animation
            anim = actor.get("animation")
            if not anim:
                issues.append(Issue("warning", sid, f"actors[{ai}].animation",
                    f"Actor '{atype}' has no 'animation' field. Frontend will default to idle."))
            elif anim not in VALID_ANIMATIONS:
                issues.append(Issue(
                    "error", sid, f"actors[{ai}].animation",
                    f"Invalid animation '{anim}' on actor '{atype}'. Not in valid animation list."
                ))

            # Type-specific required fields
            if atype == "molecule" and "moleculeType" not in actor:
                issues.append(Issue(
                    "error", sid, f"actors[{ai}].moleculeType",
                    "Molecule actor missing 'moleculeType'. Must be: water|co2|o2|glucose|magma|sediment|rock"
                ))
            if atype == "label" and "text" not in actor:
                issues.append(Issue(
                    "warning", sid, f"actors[{ai}].text",
                    "Label actor missing 'text' string. Label will be blank on screen."
                ))
            if atype == "arrow" and "angle" not in actor and "x1" not in actor:
                issues.append(Issue(
                    "warning", sid, f"actors[{ai}].angle",
                    "Arrow actor missing 'angle'+'length' or 'x1','y1','x2','y2'. Arrow has no direction."
                ))
            if atype == "sun" and actor.get("rays") is not True:
                issues.append(Issue(
                    "suggestion", sid, f"actors[{ai}].rays",
                    "Sun actor missing 'rays: true'. Without rays it looks like a plain circle."
                ))

            # Missing size / color
            if "size" not in actor:
                issues.append(Issue("suggestion", sid, f"actors[{ai}].size",
                    f"Actor '{atype}' has no 'size'. Frontend will use default — may look inconsistent."))
            if "color" not in actor:
                issues.append(Issue("suggestion", sid, f"actors[{ai}].color",
                    f"Actor '{atype}' has no 'color'. Frontend will use default color."))

    # ── Total duration mismatch ───────────────────────────────────────────────
    claimed = script.get("duration", 0)
    computed = sum(s.get("duration", 0) for s in scenes if isinstance(s, dict))
    if abs(claimed - computed) > 100:
        issues.append(Issue(
            "error", None, "duration",
            f"script.duration={claimed} but sum of scene durations={computed}. "
            f"Frontend will cut off or pad the animation incorrectly."
        ))

    # Sort: errors first, then warnings, then suggestions
    order = {"error": 0, "warning": 1, "suggestion": 2}
    issues.sort(key=lambda i: order.get(i.severity, 3))
    return [i.to_dict() for i in issues]


def _severity_summary(issues: list[dict]) -> dict:
    counts = {"error": 0, "warning": 0, "suggestion": 0}
    for i in issues:
        counts[i.get("severity", "suggestion")] = counts.get(i.get("severity", "suggestion"), 0) + 1
    return counts


# ─── AI Repair Prompt ─────────────────────────────────────────────────────────

def _build_repair_prompt(
    script: dict,
    issues: list[dict],
    cognitive_load: str,
    concept: str | None,
) -> str:
    """Build the Gemini repair prompt embedding the audit report."""

    error_list = "\n".join(
        f"  [{i['severity'].upper()}] Scene '{i.get('scene_id', 'root')}' → {i['field']}: {i['message']}"
        for i in issues
    )
    script_json = json.dumps(script, indent=2)
    load = cognitive_load.upper()
    concept_hint = concept or script.get("title", "unknown concept")

    return f"""You are a senior educational animation engineer and cognitive science expert.

An animation script for "{concept_hint}" (cognitive load: {load}) has been audited.
Your task: FIX ALL ISSUES and return a production-ready, educationally effective script.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIT REPORT — {len(issues)} issues found:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{error_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL SCRIPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{script_json}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
COGNITIVE LOAD = {load} — STRUCTURAL REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{"LOW:  7–9 scenes. MAX 2 actors/scene. ONE actor per idea. NO arrows. NO formulas. SLOW. Isolated focus." if load == "LOW" else ""}
{"MEDIUM: 5–7 scenes. 2–4 actors/scene. ONE cause→effect per scene. Arrow per interaction. MODERATE speed." if load == "MEDIUM" else ""}
{"HIGH:  3–5 scenes. 4–8 actors/scene. ALL processes visible simultaneously. Arrow network. Equations. FAST." if load == "HIGH" else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY FIX RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Fix EVERY error in the audit report — do not skip any.
2. Every scene must teach ONE clear idea visually (student can understand WITHOUT reading text).
3. Every actor must have: type, x (60–740), y (60–540), size (18–120), color (#RRGGBB), animation.
4. molecule → add moleculeType (water|co2|o2|glucose|magma|sediment|rock)
5. label    → add text (string) and fontSize (14–18)
6. arrow    → add angle (radians) + length (px) + thickness (2–5)
7. sun      → add rays: true
8. startTime must be CUMULATIVE (each scene = sum of all previous scene durations).
9. script.duration must EQUAL the sum of ALL scene durations.
10. Use semantically correct colors: sun=#FFD700, water=#2196F3, plant=#2E7D32, CO2=#9E9E9E, O2=#81C784.
11. Every process scene must have at least one animated actor (NOT idle, NOT appear-only).
12. Scene IDs must be unique and descriptive (e.g. "evaporation", "condensation", not "scene_1").

Valid actor types: sun, cloud, mountain, ocean, volcano, rock, plant, leaf, root, animal, cell, bacteria,
  molecule, atom, electron, proton, neutron, glucose, planet, moon, star, asteroid, comet,
  arrow, label, line, bolt, wave, thermometer

Valid animations: appear, idle, moveUp, moveDown, floatIn, floatOut, glow, shine, bubbleUp,
  rotate, pulse, wave, sway, grow, absorb, orbit, spin, vibrate, fall

Return ONLY valid JSON. No markdown. No explanation. No code fences.
The JSON must begin with the opening brace {{
"""


# ─── Public Repair Function ───────────────────────────────────────────────────

def repair_script(
    script: dict,
    cognitive_load: str = "medium",
    concept: str | None = None,
) -> dict:
    """
    Full repair pipeline:
      1. Audit (rule-based, deterministic)
      2. If issues found, call Gemini to redesign
      3. Re-audit the repaired script
      4. Return audit + repaired script

    Returns:
      {
        "issues_found": [...],
        "severity_summary": {error, warning, suggestion},
        "fix_explanation": str,
        "repaired_script": dict | None,
        "post_repair_issues": [...],
        "is_valid": bool,
      }
    """
    # Step 1: Audit
    issues = audit_script(script, cognitive_load)
    summary = _severity_summary(issues)
    n_errors = summary["error"]

    logger.info(
        "[script_repair] Audit complete: %d errors, %d warnings, %d suggestions",
        n_errors, summary["warning"], summary["suggestion"],
    )

    # Step 2: AI repair (always run if there are any errors or warnings)
    repaired: dict | None = None
    fix_explanation = "No critical issues found — script is structurally valid."

    if n_errors > 0 or summary["warning"] > 0:
        try:
            from app.services.visual.ai_generator import _generate_text, clean_json_output, validate_json_script
            prompt = _build_repair_prompt(script, issues, cognitive_load, concept)
            logger.info("[script_repair] Calling Gemini for AI repair...")
            raw = _generate_text(prompt, temperature=0.25, max_tokens=6000)
            cleaned = clean_json_output(raw)
            repaired = json.loads(cleaned)

            # Tag with cognitive_load
            repaired["cognitive_load"] = cognitive_load

            # Validate repaired script
            if not validate_json_script(repaired):
                logger.warning("[script_repair] Repaired script failed internal validation.")
                repaired = None
                fix_explanation = "AI returned a script that failed schema validation. Original script returned."
            else:
                fix_explanation = (
                    f"Fixed {n_errors} errors and {summary['warning']} warnings. "
                    f"Script redesigned per {cognitive_load.upper()} cognitive load rules."
                )
        except Exception as e:
            logger.error("[script_repair] AI repair failed: %s", e)
            fix_explanation = f"AI repair failed: {str(e)}. Original script returned with audit report."

    # Step 3: Re-audit the repaired script
    post_issues = audit_script(repaired, cognitive_load) if repaired else []
    post_summary = _severity_summary(post_issues)

    is_valid = repaired is not None and post_summary["error"] == 0

    return {
        "issues_found": issues,
        "severity_summary": summary,
        "fix_explanation": fix_explanation,
        "repaired_script": repaired or script,  # fall back to original if repair failed
        "post_repair_issues": post_issues,
        "post_repair_summary": post_summary,
        "is_valid": is_valid,
        "repair_applied": repaired is not None,
    }
