"""
Step-to-Visual Converter — Grade 6 Animation Pipeline

Converts step strings like "sun heats water" into structured visual data
ready for the animation script builder.

This module sits BETWEEN the step extractor and the scene assembler.
It uses the existing actor_mapper, animation_mapper, and layout_engine
as its resolution layer — it does NOT duplicate their logic.

Pipeline per step:
  Step string
      │
      ▼  Phase 1: Tokenise + POS-tag (rule-based, no spaCy needed)
      │  Identify: subjects (nouns) → actors
      │            predicates (verbs) → animations
      │            objects (nouns)   → secondary actors
      │
      ▼  Phase 2: Actor resolution (via actor_mapper.map_actor)
      │  Each noun token → { type, color, moleculeType, ... }
      │
      ▼  Phase 3: Animation resolution (via animation_mapper.map_animation)
      │  Each verb token → valid animation name
      │
      ▼  Phase 4: Layout assignment (via layout_engine.place_actor)
      │  Each actor → { x, y, size, color }
      │
      ▼  Output: VisualStep dict — one per step
         {
           "step_text": "sun heats water",
           "actors": [...],
           "primary_animation": "shine",
           "relationship": "emit",
           "cause": "sun",
           "effect": "water"
         }

Public API:
  step_to_visual(step: str, step_index: int) -> VisualStep
  steps_to_visual_sequence(steps: list[str]) -> list[VisualStep]
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Extended Actor Keyword Table ─────────────────────────────────────────────
#
# This is the WORD-LEVEL lookup used when parsing raw step sentences.
# It maps any word that might appear in a student-facing step sentence to
# its canonical actor name, which actor_mapper.py then fully resolves.
#
# Design rule:
#   - Keys = any natural English word a step might contain
#   - Values = canonical actor key accepted by actor_mapper.ACTOR_MAP
#   - This table is ADDITIVE — it extends actor_mapper, not replaces it.

WORD_TO_ACTOR: dict[str, str] = {
    # ── Sun / Heat / Light ────────────────────────────────────────────────────
    "sun": "sun",
    "sunlight": "sun",
    "solar": "sun",
    "heat": "sun",        # "heat" as a noun → sun is the heat source
    "light": "sun",
    "radiation": "sun",
    "rays": "sun",
    "energy": "bolt",

    # ── Water / Moisture ──────────────────────────────────────────────────────
    "water": "water",
    "moisture": "water",
    "rain": "water",
    "rainfall": "water",
    "precipitation": "water",
    "droplets": "water",
    "drops": "water",
    "h2o": "water",
    "liquid": "water",
    "vapour": "water",
    "vapor": "water",
    "steam": "water",
    "condensation": "water",
    "evaporation": "water",
    "runoff": "water",
    "river": "water",
    "lake": "water",
    "stream": "water",

    # ── Clouds / Sky ──────────────────────────────────────────────────────────
    "cloud": "cloud",
    "clouds": "cloud",
    "fog": "cloud",
    "mist": "cloud",
    "sky": "cloud",

    # ── Earth / Ground / Soil ─────────────────────────────────────────────────
    "ground": "earth",
    "earth": "earth",
    "soil": "root",
    "dirt": "root",
    "land": "earth",
    "surface": "earth",

    # ── Ocean / Sea ───────────────────────────────────────────────────────────
    "ocean": "ocean",
    "sea": "ocean",
    "seas": "ocean",
    "oceans": "ocean",

    # ── Mountains / Rock / Stone ──────────────────────────────────────────────
    "mountain": "mountain",
    "mountains": "mountain",
    "rock": "rock",
    "rocks": "rock",
    "stone": "rock",
    "stones": "rock",
    "sediment": "sediment",
    "sediments": "sediment",

    # ── Volcano / Magma / Lava ────────────────────────────────────────────────
    "volcano": "volcano",
    "volcanoes": "volcano",
    "magma": "magma",
    "lava": "magma",

    # ── Plants / Biology ─────────────────────────────────────────────────────
    "plant": "plant",
    "plants": "plant",
    "leaf": "leaf",
    "leaves": "leaf",
    "root": "root",
    "roots": "root",
    "tree": "plant",
    "trees": "plant",
    "flower": "plant",
    "grass": "plant",

    # ── Biology (cells, organisms) ────────────────────────────────────────────
    "cell": "cell",
    "cells": "cell",
    "bacteria": "bacteria",
    "organism": "plant",
    "organisms": "plant",
    "animal": "animal",
    "animals": "animal",

    # ── Chemistry ────────────────────────────────────────────────────────────
    "oxygen": "oxygen",
    "o2": "oxygen",
    "carbon": "co2",
    "co2": "co2",
    "dioxide": "co2",
    "glucose": "glucose",
    "sugar": "glucose",
    "atom": "atom",
    "atoms": "atom",
    "molecule": "molecule",
    "molecules": "molecule",
    "electron": "electron",
    "electrons": "electron",
    "proton": "proton",
    "neutron": "neutron",

    # ── Astronomy ─────────────────────────────────────────────────────────────
    "moon": "moon",
    "planet": "planet",
    "planets": "planet",
    "star": "star",
    "stars": "star",
    "asteroid": "asteroid",
    "comet": "comet",
    "gravity": "earth",    # gravity concept → earth actor
    "force": "bolt",
    "orbit": "moon",

    # ── Physics / Energy ─────────────────────────────────────────────────────
    "electricity": "bolt",
    "electric": "bolt",
    "current": "electron",
    "charge": "electron",
    "wave": "wave",
    "waves": "wave",
    "sound": "wave",
    "temperature": "thermometer",
    "pressure": "bolt",
}


# ─── Extended Animation Keyword Table ─────────────────────────────────────────
#
# Maps any verb or action word that might appear in a step sentence
# to a valid animation name from VALID_ANIMATIONS.
#
# Design rule:
#   - Keys = base verb forms (+ common inflections)
#   - Values = valid animation name (must be in animation_mapper.VALID_ANIMATIONS)
#   - Priority: most specific meaning wins (e.g. "evaporate" → "bubbleUp", not "moveUp")

VERB_TO_ANIMATION: dict[str, str] = {
    # ── Rising / Upward movement ──────────────────────────────────────────────
    "rise": "moveUp",
    "rises": "moveUp",
    "risen": "moveUp",
    "rising": "moveUp",
    "ascend": "moveUp",
    "ascends": "moveUp",
    "lift": "moveUp",
    "lifts": "moveUp",
    "evaporate": "bubbleUp",
    "evaporates": "bubbleUp",
    "evaporating": "bubbleUp",
    "evaporation": "bubbleUp",
    "bubble": "bubbleUp",
    "bubbles": "bubbleUp",
    "float": "floatIn",
    "floats": "floatIn",
    "floating": "floatIn",

    # ── Falling / Downward movement ───────────────────────────────────────────
    "fall": "fall",
    "falls": "fall",
    "falling": "fall",
    "fallen": "fall",
    "drop": "fall",
    "drops": "fall",
    "rain": "moveDown",
    "rains": "moveDown",
    "pour": "moveDown",
    "pours": "moveDown",
    "sink": "moveDown",
    "sinks": "moveDown",
    "descend": "moveDown",
    "descends": "moveDown",
    "flow": "moveDown",
    "flows": "moveDown",
    "flowing": "moveDown",
    "run": "moveDown",
    "runs": "moveDown",
    "drain": "moveDown",
    "drains": "moveDown",
    "seep": "moveDown",
    "seeps": "moveDown",

    # ── Forming / Appearing ───────────────────────────────────────────────────
    "form": "appear",
    "forms": "appear",
    "formed": "appear",
    "forming": "appear",
    "appear": "appear",
    "appears": "appear",
    "create": "appear",
    "creates": "appear",
    "make": "appear",
    "makes": "appear",
    "build": "grow",
    "builds": "grow",
    "collect": "grow",
    "collects": "grow",
    "gather": "grow",
    "gathers": "grow",
    "accumulate": "grow",
    "accumulates": "grow",
    "grow": "grow",
    "grows": "grow",

    # ── Heating / Energy emission ─────────────────────────────────────────────
    "heat": "shine",
    "heats": "shine",
    "heating": "shine",
    "warm": "shine",
    "warms": "shine",
    "shine": "shine",
    "shines": "shine",
    "glow": "glow",
    "glows": "glow",
    "emit": "shine",
    "emits": "shine",
    "radiate": "shine",
    "radiates": "shine",
    "light": "shine",
    "lights": "shine",

    # ── Absorbing / Taking in ─────────────────────────────────────────────────
    "absorb": "absorb",
    "absorbs": "absorb",
    "absorbing": "absorb",
    "take": "absorb",
    "takes": "absorb",
    "draw": "absorb",
    "draws": "absorb",
    "pull": "absorb",
    "pulls": "absorb",
    "attract": "absorb",
    "attracts": "absorb",

    # ── Pulsing / Energy release ──────────────────────────────────────────────
    "pulse": "pulse",
    "pulses": "pulse",
    "release": "pulse",
    "releases": "pulse",
    "push": "pulse",
    "pushes": "pulse",
    "react": "pulse",
    "reacts": "pulse",
    "explode": "pulse",
    "explodes": "pulse",
    "erupt": "pulse",
    "erupts": "pulse",
    "vibrate": "vibrate",
    "vibrates": "vibrate",
    "shake": "vibrate",
    "shakes": "vibrate",

    # ── Rotating / Orbiting ───────────────────────────────────────────────────
    "rotate": "rotate",
    "rotates": "rotate",
    "spin": "spin",
    "spins": "spin",
    "orbit": "orbit",
    "orbits": "orbit",
    "revolve": "orbit",
    "revolves": "orbit",
    "turn": "rotate",
    "turns": "rotate",
    "circle": "orbit",
    "circles": "orbit",

    # ── Swaying / Waving ─────────────────────────────────────────────────────
    "sway": "sway",
    "sways": "sway",
    "wave": "wave",
    "waves": "wave",
    "blow": "sway",
    "blows": "sway",

    # ── Idle / Resting ────────────────────────────────────────────────────────
    "stay": "idle",
    "stays": "idle",
    "rest": "idle",
    "rests": "idle",
    "remain": "idle",
    "remains": "idle",
    "sit": "idle",
    "sits": "idle",
    "is": "idle",
    "are": "idle",
}


# ─── Relationship mapper ───────────────────────────────────────────────────────
# Maps animation names to relationship type used in animations[] array.
# This tells the frontend HOW two actors relate (not just what each does).

ANIMATION_TO_RELATIONSHIP: dict[str, str] = {
    "shine": "emit",
    "glow": "emit",
    "pulse": "emit",
    "bubbleUp": "flow",
    "moveUp": "flow",
    "moveDown": "flow",
    "fall": "flow",
    "floatIn": "flow",
    "floatOut": "flow",
    "absorb": "absorb",
    "grow": "transform",
    "appear": "transform",
    "orbit": "orbit",
    "rotate": "orbit",
    "spin": "orbit",
    "vibrate": "emit",
    "wave": "emit",
    "idle": "emit",
    "sway": "emit",
}


# ─── Stop words (ignored during token extraction) ────────────────────────────

_STOP_WORDS: set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "into", "onto", "from", "through", "by", "with", "and", "or",
    "as", "it", "its", "this", "that", "in", "on", "at", "to",
    "of", "up", "down", "out", "over", "then", "first", "next",
    "finally", "after", "before", "when", "also",
}


# ─── Sentence tokeniser ────────────────────────────────────────────────────────

def _tokenise_step(step: str) -> list[str]:
    """
    Lowercase and tokenise a step string.
    Strips punctuation and stop words. Returns meaningful content words only.

    Example:
        "First, the sun heats water." → ["sun", "heats", "water"]
    """
    # Remove step prefix patterns ("First,", "Next,", "Then,")
    step = re.sub(r'^(first|next|then|after that|finally|also)[,\s]+', '', step.strip(), flags=re.IGNORECASE)
    # Lowercase and remove punctuation
    step = re.sub(r'[^\w\s]', ' ', step.lower())
    # Tokenise and remove stop words
    tokens = [t for t in step.split() if t and t not in _STOP_WORDS]
    return tokens


# ─── Actor and verb extraction ───────────────────────────────────────────────

def _extract_actors_from_tokens(tokens: list[str]) -> list[str]:
    """
    Extract actor canonical names from token list.
    Returns unique actor names in order of appearance.
    Deduplicates actors pointing to the same canonical key.
    """
    seen: set[str] = set()
    actors: list[str] = []
    for token in tokens:
        canonical = WORD_TO_ACTOR.get(token)
        if canonical and canonical not in seen:
            seen.add(canonical)
            actors.append(canonical)
    return actors


def _extract_verbs_from_tokens(tokens: list[str]) -> list[str]:
    """
    Extract animation-mapped verbs from token list, in order.
    Filters out "idle" from multi-verb steps (it's a fallback, not a meaningful action).
    """
    animations: list[str] = []
    for token in tokens:
        anim = VERB_TO_ANIMATION.get(token)
        if anim and anim not in animations:
            animations.append(anim)
    # If only "idle" found, keep it — but filter it when better options exist
    non_idle = [a for a in animations if a != "idle"]
    return non_idle if non_idle else (animations or ["idle"])


# ─── Primary animation selection ─────────────────────────────────────────────

def _select_primary_animation(animations: list[str], actors: list[str]) -> str:
    """
    Select the single best animation for the primary actor in this step.

    Priority order:
      1. First non-idle animation found (directly describes the action)
      2. Actor-type default if no verb matched (e.g. sun → shine)
      3. "idle" as absolute fallback
    """
    # Actor-type animation defaults (when no verb matched)
    ACTOR_DEFAULT_ANIMATION: dict[str, str] = {
        "sun": "shine",
        "cloud": "floatIn",
        "water": "bubbleUp",
        "ocean": "wave",
        "rain": "moveDown",
        "volcano": "pulse",
        "mountain": "idle",
        "rock": "idle",
        "earth": "idle",
        "plant": "grow",
        "leaf": "glow",
        "root": "absorb",
        "cell": "pulse",
        "electron": "rotate",
        "bolt": "pulse",
        "wave": "wave",
        "moon": "orbit",
        "star": "shine",
    }

    if animations and animations[0] != "idle":
        return animations[0]

    # Fall back to actor-type default for the primary actor
    if actors:
        primary_actor = actors[0]
        return ACTOR_DEFAULT_ANIMATION.get(primary_actor, "idle")

    return "idle"


# ─── Full actor object builder ────────────────────────────────────────────────

def _build_actor_objects(
    actor_names: list[str],
    primary_animation: str,
    secondary_animations: list[str],
) -> list[dict]:
    """
    Build complete actor objects for each actor name.
    Resolves type, color, position via existing mapper + layout engine.
    Returns list of actor dicts ready for animation script.
    """
    from app.services.visual.actor_mapper import map_actor, validate_actor_type
    from app.services.visual.layout_engine import place_actor, get_actor_properties

    total = len(actor_names)
    actor_objects: list[dict] = []

    for idx, canonical_name in enumerate(actor_names):
        actor_config = map_actor(canonical_name)
        if not actor_config:
            logger.warning("[step_to_visual] Could not map actor: '%s'", canonical_name)
            continue

        actor_type = actor_config.get("type", "")
        if not validate_actor_type(actor_type):
            logger.warning("[step_to_visual] Invalid actor type '%s' for '%s'", actor_type, canonical_name)
            continue

        # Assign animation: primary actor gets primary, others get secondary or idle
        if idx == 0:
            animation = primary_animation
        elif idx < len(secondary_animations):
            animation = secondary_animations[idx]
        else:
            animation = "idle"

        # Resolve position and visual properties
        placement = place_actor(actor_type, idx, total, {"domain": actor_config.get("category", "generic")})
        props = get_actor_properties(actor_type, {
            "moleculeType": actor_config.get("moleculeType"),
            "domain": actor_config.get("category"),
        })

        actor_obj: dict = {
            "type": actor_type,
            "x": placement["x"],
            "y": placement["y"],
            "size": placement["size"],
            "color": placement["color"],
            "animation": animation,
        }

        # Type-specific required fields (prevents frontend errors)
        if actor_type == "sun":
            actor_obj["rays"] = True
        elif actor_type == "molecule":
            actor_obj["moleculeType"] = actor_config.get("moleculeType", "water")
        elif actor_type == "arrow":
            actor_obj["angle"] = props.get("angle", 1.5708)   # default: downward
            actor_obj["length"] = props.get("length", 100)
            actor_obj["thickness"] = 3
        elif actor_type == "label":
            actor_obj["text"] = canonical_name.capitalize()
            actor_obj["fontSize"] = props.get("fontSize", 16)
        elif actor_type == "root":
            actor_obj["depth"] = props.get("depth", 80)
            actor_obj["width"] = props.get("width", 100)
            actor_obj["branches"] = props.get("branches", 6)
        elif actor_type == "leaf":
            actor_obj["angle"] = props.get("angle", 0)
        elif actor_type == "cell":
            actor_obj["cellType"] = "plant"
            actor_obj["showLabels"] = True

        actor_objects.append(actor_obj)

    return actor_objects


# ─── Relationship builder ─────────────────────────────────────────────────────

def _build_relationship(
    actor_objects: list[dict],
    primary_animation: str,
    step_duration_ms: int,
) -> Optional[dict]:
    """
    Build a single animations[] entry showing how the primary actor
    relates to the secondary actor (cause → effect).

    Returns None if fewer than 2 actors (no relationship to show).
    """
    if len(actor_objects) < 2:
        return None

    relationship = ANIMATION_TO_RELATIONSHIP.get(primary_animation, "emit")
    # Use type as ID reference (script_builder assigns actual IDs)
    from_id = f"{actor_objects[0]['type']}_1"
    to_id = f"{actor_objects[1]['type']}_1"

    return {
        "type": relationship,
        "from": from_id,
        "to": to_id,
        "duration": step_duration_ms,
    }


# ─── VisualStep dataclass ─────────────────────────────────────────────────────

def _make_visual_step(
    step_text: str,
    step_index: int,
    actor_objects: list[dict],
    primary_animation: str,
    cause_actor: Optional[str],
    effect_actor: Optional[str],
    relationship: Optional[dict],
    step_duration_ms: int,
) -> dict:
    """Assemble the final VisualStep dict."""
    return {
        "id": f"step_{step_index + 1}",
        "step_text": step_text,
        "actors": actor_objects,
        "primary_animation": primary_animation,
        "relationship": relationship,
        "cause": cause_actor,
        "effect": effect_actor,
        "duration_ms": step_duration_ms,
    }


# ─── Public API ──────────────────────────────────────────────────────────────

def step_to_visual(step: str, step_index: int = 0, step_duration_ms: int = 5000) -> dict:
    """
    Convert a single step string into a VisualStep dict.

    Args:
        step:             A simplified step string, e.g. "sun heats water".
        step_index:       0-based position of this step in the sequence.
        step_duration_ms: Duration in milliseconds for this step's scene (default 5s).

    Returns:
        VisualStep dict:
        {
          "id": "step_1",
          "step_text": "sun heats water",
          "actors": [
            { "type": "sun", "x": 700, "y": 80, "size": 50, "color": "#FFD700",
              "animation": "shine", "rays": true },
            { "type": "molecule", "x": 280, "y": 300, "size": 25, "color": "#2196F3",
              "animation": "bubbleUp", "moleculeType": "water" }
          ],
          "primary_animation": "shine",
          "relationship": { "type": "emit", "from": "sun_1", "to": "molecule_1", "duration": 5000 },
          "cause": "sun",
          "effect": "water",
          "duration_ms": 5000
        }

    Example:
        >>> step_to_visual("sun heats water", step_index=0)
        >>> step_to_visual("water rises as vapour", step_index=1)
        >>> step_to_visual("cloud forms in the sky", step_index=2)
        >>> step_to_visual("rain falls back to earth", step_index=3)
    """
    if not step or not step.strip():
        logger.warning("[step_to_visual] Empty step at index %d.", step_index)
        return _make_visual_step(step, step_index, [], "idle", None, None, None, step_duration_ms)

    tokens = _tokenise_step(step)
    logger.debug("[step_to_visual] Step %d tokens: %s", step_index, tokens)

    # Phase 1: Extract actors and animations from tokens
    actor_names = _extract_actors_from_tokens(tokens)
    animations = _extract_verbs_from_tokens(tokens)

    # Phase 2: Select primary animation
    primary_animation = _select_primary_animation(animations, actor_names)
    secondary_animations = [a for a in animations if a != primary_animation]

    # Phase 3: Identify cause and effect
    cause_actor = actor_names[0] if actor_names else None
    effect_actor = actor_names[1] if len(actor_names) > 1 else None

    # Phase 4: Build actor objects (resolved via existing mappers)
    actor_objects = _build_actor_objects(actor_names, primary_animation, secondary_animations)

    # Phase 5: Build relationship
    relationship = _build_relationship(actor_objects, primary_animation, step_duration_ms)

    visual_step = _make_visual_step(
        step_text=step,
        step_index=step_index,
        actor_objects=actor_objects,
        primary_animation=primary_animation,
        cause_actor=cause_actor,
        effect_actor=effect_actor,
        relationship=relationship,
        step_duration_ms=step_duration_ms,
    )

    logger.info(
        "[step_to_visual] Step %d → actors: %s, anim: %s, rel: %s→%s",
        step_index,
        [a.get("type") for a in actor_objects],
        primary_animation,
        cause_actor,
        effect_actor,
    )
    return visual_step


def steps_to_visual_sequence(
    steps: list[str],
    step_duration_ms: int = 5000,
) -> list[dict]:
    """
    Convert a list of step strings into an ordered sequence of VisualStep dicts.

    Args:
        steps:            List of step strings from step_extractor.extract_steps().
        step_duration_ms: Duration per step in milliseconds (default 5s each).

    Returns:
        List of VisualStep dicts, one per step, in original order.

    Example:
        >>> steps = [
        ...     "First, the sun heats water.",
        ...     "Next, water rises as vapour.",
        ...     "Then, vapour forms clouds.",
        ...     "After that, clouds release rain.",
        ...     "Finally, rain falls back to earth.",
        ... ]
        >>> visual_sequence = steps_to_visual_sequence(steps)
        >>> # Each item is a VisualStep dict ready for script_builder.build_script()
    """
    if not steps:
        logger.warning("[step_to_visual] Empty steps list.")
        return []

    sequence = []
    for i, step in enumerate(steps):
        visual = step_to_visual(step, step_index=i, step_duration_ms=step_duration_ms)
        sequence.append(visual)

    logger.info("[step_to_visual] Converted %d steps → %d visual steps.", len(steps), len(sequence))
    return sequence
