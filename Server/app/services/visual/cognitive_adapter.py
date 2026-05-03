"""
Cognitive Complexity Adapter — Grade 6 Animation Pipeline

Takes an already-assembled AnimationScript and transforms its scenes
IN-PLACE to match the target cognitive load level.

Three distinct adaptation strategies:

  LOW  (OVERLOAD)  → Strip down. 1–2 actors. Slow pace. No arrows. No
                     formulas. Isolated, focused, high-contrast visuals.
                     Each scene teaches exactly ONE idea.

  MEDIUM (OPTIMAL) → Balance. 2–3 actors. Moderate pace. One cause→effect
                     arrow per scene. Labels allowed. No formulas except
                     summary scene.

  HIGH (LOW_LOAD)  → Enrich. 3–5 actors. Fast pace. Arrow network.
                     Formulas, labels, simultaneous processes. Full system
                     visible in summary scene.

This module DOES NOT call any LLM. It is pure deterministic Python.

Integration:
  from app.services.visual.cognitive_adapter import adapt_script

  adapted = adapt_script(script, cognitive_load="low")

Existing files used (not duplicated):
  - constants.py   → scene duration values per state
  - script_builder.py → recomputes startTime after duration changes
  - script_repair.py  → structural rules (_CL_RULES) referenced here
"""

from __future__ import annotations

import copy
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


# ─── Structural Rules per Level ───────────────────────────────────────────────
# These mirror _CL_RULES in script_repair.py but are used here for ADAPTATION
# (building correct scripts), not just auditing (checking existing ones).

_LEVEL_RULES: dict[str, dict] = {
    "low": {
        # Visual complexity
        "max_actors":          2,       # Strict: 1–2 actors only
        "min_actors":          1,
        "arrow_allowed":       False,   # No arrows (imply relationships = too complex)
        "formula_allowed":     False,   # No scientific formulas
        "label_allowed":       True,    # Object name label only (max 2 words)
        "max_label_words":     2,
        "animations_allowed":  {"appear", "idle", "grow", "pulse", "sway", "glow", "shine"},
        "fallback_animation":  "idle",
        # Timing
        "scene_duration_ms":   5500,    # Slow: student needs time to absorb one thing
        "min_duration_ms":     4500,
        "max_duration_ms":     7000,
        # Actor sizing — large actors on LOW (isolated focus = fills canvas)
        "size_multiplier":     1.4,     # Actors 40% larger than default
        "max_size":            100,
        # Scene structure
        "actors_per_scene":    "1–2",
        "priority":            "subject",   # Keep the most important actor (position 0)
    },
    "medium": {
        "max_actors":          3,
        "min_actors":          2,
        "arrow_allowed":       True,    # One arrow per scene showing cause→effect
        "formula_allowed":     False,   # Only in final summary scene
        "label_allowed":       True,
        "max_label_words":     3,
        "animations_allowed":  {
            "appear", "idle", "grow", "pulse", "sway", "glow", "shine",
            "moveUp", "moveDown", "floatIn", "floatOut", "bubbleUp", "fall",
            "absorb", "rotate",
        },
        "fallback_animation":  "pulse",
        "scene_duration_ms":   5000,
        "min_duration_ms":     4000,
        "max_duration_ms":     7000,
        "size_multiplier":     1.0,
        "max_size":            90,
        "actors_per_scene":    "2–3",
        "priority":            "cause_effect",  # Keep cause + effect + one arrow
    },
    "high": {
        "max_actors":          5,       # Allow dense scenes
        "min_actors":          3,
        "arrow_allowed":       True,    # Multiple arrows showing causal network
        "formula_allowed":     True,    # Equations and labels encouraged
        "label_allowed":       True,
        "max_label_words":     6,       # Can include formula text
        "animations_allowed":  {
            "appear", "idle", "grow", "pulse", "sway", "glow", "shine",
            "moveUp", "moveDown", "floatIn", "floatOut", "bubbleUp", "fall",
            "absorb", "rotate", "orbit", "spin", "vibrate", "wave",
        },
        "fallback_animation":  "pulse",
        "scene_duration_ms":   4000,   # Faster pace: student can handle density
        "min_duration_ms":     3500,
        "max_duration_ms":     6000,
        "size_multiplier":     0.75,   # Smaller actors to fit more on screen
        "max_size":            70,
        "actors_per_scene":    "3–5",
        "priority":            "system",    # Keep all actors — show full system
    },
}


# ─── Actor priority weights ────────────────────────────────────────────────────
# When trimming actors to meet max_actors, this decides which to keep.
# Higher weight = more likely to be kept.

_ACTOR_KEEP_PRIORITY: dict[str, int] = {
    # Primary actors (always keep if possible)
    "sun": 10, "earth": 10, "plant": 10, "volcano": 10, "ocean": 10,
    "cloud": 9, "leaf": 9, "moon": 9, "planet": 9, "mountain": 9,
    # Secondary actors
    "root": 7, "cell": 7, "star": 7, "atom": 7, "molecule": 7,
    "electron": 6, "bacteria": 6, "animal": 6, "rock": 6,
    "proton": 5, "neutron": 5, "glucose": 5, "bolt": 5, "wave": 5,
    # Visual aids — lowest priority (removed first under LOW)
    "arrow": 3, "label": 4, "line": 2, "graph": 2,
    "number": 3, "thermometer": 3,
}

_ANIMATION_COMPLEXITY: dict[str, int] = {
    "idle": 1, "appear": 1,
    "sway": 2, "pulse": 2, "glow": 2, "grow": 2, "shine": 2,
    "moveUp": 3, "moveDown": 3, "fall": 3, "floatIn": 3, "floatOut": 3,
    "absorb": 4, "bubbleUp": 4, "rotate": 4, "wave": 4,
    "orbit": 5, "spin": 5, "vibrate": 5,
}


# ─── Utility helpers ──────────────────────────────────────────────────────────

def _normalize_level(level: str) -> str:
    """Map any cognitive level string to 'low' | 'medium' | 'high'."""
    raw = (level or "medium").lower().strip()
    if raw in {"low", "overload", "tier3", "tier 3", "beginner"}:
        return "low"
    if raw in {"high", "low_load", "lowload", "enrichment", "advanced"}:
        return "high"
    return "medium"


def _actor_priority(actor: dict) -> int:
    """Return keep-priority for an actor. Higher = keep preferentially."""
    atype = actor.get("type", "label")
    return _ACTOR_KEEP_PRIORITY.get(atype, 4)


def _animation_complexity(animation: str) -> int:
    return _ANIMATION_COMPLEXITY.get(animation, 3)


def _clamp_size(size: float | int | None, rules: dict) -> int:
    """Apply size multiplier and clamp to valid range."""
    raw = size if isinstance(size, (int, float)) and size > 0 else 40
    scaled = raw * rules["size_multiplier"]
    return max(18, min(int(scaled), rules["max_size"]))


def _truncate_label(text: str, max_words: int) -> str:
    words = (text or "").split()
    return " ".join(words[:max_words]) if words else ""


def _recompute_start_times(scenes: list[dict]) -> list[dict]:
    """Recompute all startTime values from scratch after duration changes."""
    current = 0
    for scene in scenes:
        scene["startTime"] = current
        current += scene.get("duration", 5000)
    return scenes


# ─── Scene-level adaptation functions ────────────────────────────────────────

def _adapt_actors_for_low(actors: list[dict], rules: dict) -> list[dict]:
    """
    LOW level actor adaptation:
    - Remove all arrows (they imply relationships — too complex)
    - Remove all formula labels
    - Keep only the top 1–2 most important actors (by priority weight)
    - Scale remaining actors up (large = isolated focus)
    - Downgrade complex animations to simple ones
    """
    # Step 1: Remove arrows (forbidden at LOW)
    non_arrows = [a for a in actors if a.get("type") != "arrow"]

    # Step 2: Remove formula labels (contain numbers, symbols, subscripts)
    def _is_formula(actor: dict) -> bool:
        if actor.get("type") not in ("label", "number"):
            return False
        text = actor.get("text", "")
        return any(ch in text for ch in "0123456789=₂₃₆₁₂₀CO₂H")

    non_formula = [a for a in non_arrows if not _is_formula(a)]
    if not non_formula:
        non_formula = non_arrows  # safety: keep something

    # Step 3: Sort by priority and keep max 2
    sorted_actors = sorted(non_formula, key=_actor_priority, reverse=True)
    kept = sorted_actors[:rules["max_actors"]]

    # Step 4: Scale up sizes + simplify animations
    allowed = rules["animations_allowed"]
    result = []
    for actor in kept:
        a = dict(actor)
        a["size"] = _clamp_size(a.get("size"), rules)
        anim = a.get("animation", "idle")
        if anim not in allowed:
            # Downgrade to a simple animation based on complexity
            a["animation"] = rules["fallback_animation"]
        result.append(a)

    return result


def _adapt_actors_for_medium(actors: list[dict], rules: dict) -> list[dict]:
    """
    MEDIUM level actor adaptation:
    - Keep max 3 actors: prefer 1 cause + 1 effect + 1 arrow
    - One arrow is allowed and encouraged to show cause→effect
    - Remove duplicate arrows (keep only one)
    - Truncate label text to 3 words
    - Ensure at least one non-idle animation
    """
    # Separate by type
    arrows = [a for a in actors if a.get("type") == "arrow"]
    labels = [a for a in actors if a.get("type") in ("label", "number")]
    others = [a for a in actors if a.get("type") not in ("arrow", "label", "number")]

    # Sort other actors by priority
    others_sorted = sorted(others, key=_actor_priority, reverse=True)

    # Budget: max 3 total
    budget = rules["max_actors"]
    kept: list[dict] = []

    # Always keep top 2 content actors (cause + effect)
    kept.extend(others_sorted[:2])
    budget -= len(kept)

    # Keep one arrow if we have budget
    if arrows and budget > 0 and rules["arrow_allowed"]:
        kept.append(arrows[0])  # only one arrow for MEDIUM
        budget -= 1

    # Fill remaining budget with labels (max 1)
    if labels and budget > 0:
        kept.append(labels[0])

    # Apply size normalization and animation checks
    allowed = rules["animations_allowed"]
    result = []
    for actor in kept:
        a = dict(actor)
        a["size"] = _clamp_size(a.get("size"), rules)
        # Truncate label text
        if a.get("type") in ("label", "number") and a.get("text"):
            a["text"] = _truncate_label(a["text"], rules["max_label_words"])
        # Downgrade unsupported animations
        anim = a.get("animation", "idle")
        if anim not in allowed:
            a["animation"] = rules["fallback_animation"]
        result.append(a)

    # Ensure at least one non-static animation in the scene
    animations_in_scene = [a.get("animation", "idle") for a in result]
    if all(anim in {"idle", "appear"} for anim in animations_in_scene) and result:
        result[0]["animation"] = "pulse"  # promote primary actor

    return result


def _adapt_actors_for_high(actors: list[dict], rules: dict) -> list[dict]:
    """
    HIGH level actor adaptation:
    - Allow up to 5 actors (full system view)
    - Keep all arrows (network of cause→effect)
    - Keep all labels including formulas
    - Scale actors DOWN (smaller = more fit on screen simultaneously)
    - Promote complex animations where simple ones exist
    - Ensure minimum 3 actors (add labels if needed)
    """
    # Sort by priority but keep more
    sorted_actors = sorted(actors, key=_actor_priority, reverse=True)
    kept = sorted_actors[:rules["max_actors"]]

    allowed = rules["animations_allowed"]
    result = []
    for actor in kept:
        a = dict(actor)
        a["size"] = _clamp_size(a.get("size"), rules)
        anim = a.get("animation", "idle")

        # Promote overly simple animations on content actors
        atype = a.get("type", "")
        if anim in {"idle", "appear"} and atype not in ("arrow", "label", "number", "line"):
            # Upgrade to a domain-appropriate animation
            a["animation"] = _promote_animation(atype)
        elif anim not in allowed:
            a["animation"] = rules["fallback_animation"]
        result.append(a)

    # HIGH must have ≥ 3 actors — pad with system-view label if short
    if len(result) < rules["min_actors"] and result:
        while len(result) < rules["min_actors"]:
            result.append({
                "type": "label",
                "x": 400, "y": 260,
                "size": 20,
                "color": "#2563EB",
                "animation": "appear",
                "text": "Full System",
                "fontSize": 16,
            })
            if len(result) >= rules["min_actors"]:
                break

    return result


def _promote_animation(actor_type: str) -> str:
    """Promote a static actor to a more active animation for HIGH load scenes."""
    PROMOTIONS: dict[str, str] = {
        "sun": "shine", "star": "shine", "bolt": "pulse",
        "plant": "grow", "leaf": "glow", "root": "absorb",
        "cloud": "floatIn", "ocean": "wave", "volcano": "pulse",
        "mountain": "idle",
        "molecule": "bubbleUp", "atom": "rotate", "electron": "orbit",
        "cell": "pulse", "bacteria": "pulse", "animal": "sway",
        "earth": "idle", "moon": "orbit", "planet": "rotate",
        "wave": "wave", "thermometer": "pulse",
    }
    return PROMOTIONS.get(actor_type, "pulse")


def _adapt_scene_duration(scene: dict, rules: dict) -> int:
    """
    Calculate adapted scene duration in ms.
    Considers:
      - Base duration per cognitive level
      - Slight increase for scenes with more actors (need time to track)
      - Text length (reading time)
    """
    base = rules["scene_duration_ms"]
    actor_count = len(scene.get("actors", []))
    text_len = len(scene.get("text", ""))

    # Actor complexity bonus
    actor_bonus = max(0, actor_count - 1) * 200   # +200ms per extra actor

    # Text reading time bonus
    text_bonus = 0
    if text_len > 60:
        text_bonus = 400
    if text_len > 100:
        text_bonus = 800

    raw = base + actor_bonus + text_bonus
    return max(rules["min_duration_ms"], min(int(raw), rules["max_duration_ms"]))


def _adapt_animations_array(
    animations: list[dict],
    actor_ids: set[str],
    rules: dict,
    level: str,          # explicit parameter — no global state
) -> list[dict]:
    """
    Clean up the animations[] (AnimationLink) array after actor trimming.

    Rules:
      LOW:    Remove all animations[] entries (no relationship arrows)
      MEDIUM: Keep only one animation entry (the primary cause→effect)
      HIGH:   Keep all valid entries that reference existing actor ids
    """
    if not animations:
        return []

    if level == "low":
        return []  # LOW shows isolated actors — no relationship animations

    valid = [
        a for a in animations
        if isinstance(a, dict)
        and a.get("from") in actor_ids
        and a.get("to") in actor_ids
    ]

    if level == "medium":
        return valid[:1]  # Only one cause→effect link for MEDIUM

    return valid  # HIGH: keep all valid links


# ─── Scene text adapter ───────────────────────────────────────────────────────

def _adapt_scene_text(text: str, level: str) -> str:
    """
    Enforce text length constraints per cognitive level.

    LOW:    Max 12 words. Simple subject-verb sentence.
    MEDIUM: Max 18 words. One sentence.
    HIGH:   Max 25 words. Can include scientific terms.
    """
    if not text:
        return text

    max_words = {"low": 12, "medium": 18, "high": 25}.get(level, 18)
    words = text.split()
    if len(words) <= max_words:
        return text

    truncated = " ".join(words[:max_words])
    # Ensure it ends with a period
    if not truncated.endswith("."):
        truncated = truncated.rstrip(".,;:!?") + "."
    return truncated


# ─── Focus line adapter ───────────────────────────────────────────────────────

def _adapt_focus(focus: str, level: str) -> str:
    """
    Adapt the scene focus field (max 6 words always, but tone varies).
    LOW:    Max 4 words ("Sun shines light")
    MEDIUM: Max 6 words ("Sun emits light to leaf")
    HIGH:   Max 6 words, scientific terms OK
    """
    max_words = {"low": 4, "medium": 6, "high": 6}.get(level, 6)
    words = (focus or "").split()
    return " ".join(words[:max_words])


# ─── Scene-level entry point ──────────────────────────────────────────────────

def _adapt_scene(scene: dict, level: str, rules: dict, scene_index: int) -> dict:
    """
    Adapt a single scene dict to the target cognitive level.
    Returns a new scene dict (does not mutate original).
    """
    s = copy.deepcopy(scene)

    # 1. Adapt actors based on level
    actors = s.get("actors", [])
    if level == "low":
        adapted_actors = _adapt_actors_for_low(actors, rules)
    elif level == "high":
        adapted_actors = _adapt_actors_for_high(actors, rules)
    else:
        adapted_actors = _adapt_actors_for_medium(actors, rules)

    s["actors"] = adapted_actors

    # 2. Adapt animations[] to match remaining actor ids
    actor_ids = {
        a.get("id", f"{a.get('type', 'actor')}_{i}")
        for i, a in enumerate(adapted_actors)
    }
    s["animations"] = _adapt_animations_array(
        s.get("animations", []),
        actor_ids,
        rules,
        level,           # pass level explicitly — thread-safe
    )

    # 3. Adapt scene duration
    s["duration"] = _adapt_scene_duration(s, rules)

    # 4. Adapt text and focus
    s["text"] = _adapt_scene_text(s.get("text", ""), level)
    s["focus"] = _adapt_focus(s.get("focus", ""), level)

    # 5. Set environment hint
    env_map = {"low": "minimal", "medium": "default", "high": "rich"}
    if not s.get("environment") or s["environment"] == "default":
        s["environment"] = env_map[level]

    # 6. Set cognitive level metadata
    s.setdefault("meta", {})
    s["meta"]["cognitiveLevel"] = level
    s["meta"]["adapted"] = True
    s["meta"]["original_actor_count"] = len(actors)
    s["meta"]["adapted_actor_count"] = len(adapted_actors)

    return s


# ─── Script-level entry point (PUBLIC API) ───────────────────────────────────

def adapt_script(
    script: dict,
    cognitive_load: str = "medium",
) -> dict:
    """
    Adapt an AnimationScript dict to the target cognitive load level.

    Takes an already-assembled script (from script_builder.build_script or
    visual_planner + hybrid_generator) and transforms it in-place by:
      - Trimming or expanding actors per scene
      - Adjusting scene durations (slow for LOW, fast for HIGH)
      - Removing or adding arrows and labels
      - Recomputing all startTime values
      - Constraining text length

    Args:
        script:          AnimationScript dict with title, duration, scenes[].
        cognitive_load:  "low" | "medium" | "high" (also accepts aliases —
                         see _normalize_level).

    Returns:
        New adapted AnimationScript dict. Original is NOT mutated.

    Example:
        >>> base_script = build_script("Water Cycle", scenes, analysis)
        >>> low_script  = adapt_script(base_script, cognitive_load="low")
        >>> med_script  = adapt_script(base_script, cognitive_load="medium")
        >>> high_script = adapt_script(base_script, cognitive_load="high")

    What changes per level:

        LOW (1–2 actors, slow):
          - Max 2 actors per scene (keeps most important by priority weight)
          - No arrows (visual relationships = cognitive overload for beginners)
          - No formulas in labels
          - Animations downgraded to: appear, idle, grow, pulse, sway, glow, shine
          - Scene duration: 4500–7000ms (slow — one idea per breath)
          - Actors scaled UP (40% larger — isolated focus fills the canvas)
          - Scene text capped at 12 words
          - environment: "minimal"

        MEDIUM (2–3 actors, moderate):
          - Max 3 actors (cause + effect + one arrow)
          - One arrow per scene (shows cause→effect clearly)
          - Labels allowed (max 3 words each)
          - All common animations allowed
          - Scene duration: 4000–7000ms
          - Scene text capped at 18 words
          - environment: "default"

        HIGH (3–5 actors, fast):
          - Up to 5 actors per scene (full system visible)
          - All arrows kept (causal network)
          - Formulas and scientific labels allowed
          - Static actors promoted to active animations
          - Scene duration: 3500–6000ms (faster pace)
          - Actors scaled DOWN (smaller = more fit on screen)
          - Scene text capped at 25 words
          - environment: "rich"
    """
    if not isinstance(script, dict):
        logger.error("[cognitive_adapter] Expected dict, got %s", type(script))
        return script

    level = _normalize_level(cognitive_load)
    rules = _LEVEL_RULES[level]

    scenes = script.get("scenes", [])
    if not scenes:
        logger.warning("[cognitive_adapter] Script has no scenes to adapt.")
        return script

    logger.info(
        "[cognitive_adapter] Adapting %d scenes → level='%s' "
        "(max_actors=%d, duration=%dms)",
        len(scenes), level, rules["max_actors"], rules["scene_duration_ms"],
    )

    # Deep copy — never mutate the input
    adapted = copy.deepcopy(script)

    # Adapt each scene
    adapted_scenes = [
        _adapt_scene(scene, level, rules, idx)
        for idx, scene in enumerate(scenes)
    ]

    # Recompute all startTimes after duration changes
    adapted["scenes"] = _recompute_start_times(adapted_scenes)

    # Recompute total duration
    adapted["duration"] = sum(s.get("duration", 0) for s in adapted["scenes"])

    # Tag the script with cognitive level
    adapted["cognitive_level"] = level
    adapted["cognitive_load"] = level  # backward compat with v1 consumers

    logger.info(
        "[cognitive_adapter] Done. Total duration: %dms across %d scenes.",
        adapted["duration"], len(adapted["scenes"]),
    )
    return adapted


# ─── Convenience: adapt for all three levels at once ─────────────────────────

def adapt_script_all_levels(script: dict) -> dict[str, dict]:
    """
    Generate all three cognitive level variants of a script in one call.

    Returns:
        {
          "low":    adapted AnimationScript for LOW load,
          "medium": adapted AnimationScript for MEDIUM load,
          "high":   adapted AnimationScript for HIGH load,
        }

    Example:
        >>> base = build_script("Photosynthesis", scenes, analysis)
        >>> variants = adapt_script_all_levels(base)
        >>> variants["low"]    # send to beginner student
        >>> variants["medium"] # send to average student
        >>> variants["high"]   # send to advanced student
    """
    return {
        "low":    adapt_script(script, "low"),
        "medium": adapt_script(script, "medium"),
        "high":   adapt_script(script, "high"),
    }
