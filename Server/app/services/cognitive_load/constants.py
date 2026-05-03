"""
Cognitive Load Constants and State Definitions
===============================================

Centralizes the cognitive load level system across EduSense backend.

Research grounding:
- Sweller (1988): Working memory is limited. States mapped from
  behavioral proxies (quiz interaction signals), NOT brain activity.
- Paivio (1971) Dual Coding: visual + verbal channels processed
  in parallel; each channel has own limited capacity.
- CTML Principles (Mayer, 2009): coherence, signaling, spatial/
  temporal contiguity drive the rendering strategy.

State Definitions
-----------------

| State     | Cognitive Signal                    | Visual Strategy                |
|-----------|-------------------------------------|--------------------------------|
| OVERLOAD  | High load: accuracy <40%, errors>3  | Max 2 actors, slow pace 4.5s   |
|           | answer changes>2, long gaps         | Minimal background, clear text |
| OPTIMAL   | Normal: accuracy 40-75%, typical    | 2-4 actors, 5.5s pace          |
|           | interaction patterns                | Default background             |
| LOW_LOAD  | Under-engaged: accuracy >75%,       | 4-6 actors, 7s pace            |
|           | fast responses, few errors          | Rich background + avatar       |

Wire-format state strings (what flows across the API):
  "OVERLOAD" | "OPTIMAL" | "LOW_LOAD"

Predictor output (what the ML model returns internally):
  "High" | "Medium" | "Low"  (then mapped → OVERLOAD/OPTIMAL/LOW_LOAD)
"""

from typing import Literal

# ─── Wire Types ──────────────────────────────────────────────────────────────

CognitiveWireState = Literal["OVERLOAD", "OPTIMAL", "LOW_LOAD"]
InternalLoadLevel = Literal["High", "Medium", "Low"]

# ─── Thresholds (behavioral proxy heuristic) ─────────────────────────────────

# These are used by _predict_fallback in cognitive_load_predictor.py.
# High load ≥ 70 score points → OVERLOAD
# Medium load 40-69 → OPTIMAL
# Low load < 40 → LOW_LOAD
LOAD_HIGH_THRESHOLD = 70.0
LOAD_MEDIUM_THRESHOLD = 40.0

# ─── Animation Scene Pacing (ms) ─────────────────────────────────────────────

SCENE_DURATION_OVERLOAD = 4500   # Short scenes: less info per chunk
SCENE_DURATION_OPTIMAL = 5500    # Medium pace
SCENE_DURATION_LOW_LOAD = 7000   # Longer scenes: richer, generative
SCENE_DURATION_MIN = 3500
SCENE_DURATION_MAX = 9000

# ─── Visual Actor Limits ──────────────────────────────────────────────────────

ACTOR_LIMIT_OVERLOAD = 2         # Strict: reduce extraneous load
ACTOR_LIMIT_OPTIMAL = 4          # Moderate visual complexity
ACTOR_LIMIT_LOW_LOAD = 999       # No limit: encourage exploration

# ─── Environment Backgrounds ─────────────────────────────────────────────────

ENVIRONMENT_OVERLOAD = "minimal"    # Flat bg, minimal motion
ENVIRONMENT_OPTIMAL = "default"     # Standard context
ENVIRONMENT_LOW_LOAD = "rich"       # More motion, contextual cues

# ─── Mapping Helpers ─────────────────────────────────────────────────────────


def map_predictor_to_wire(predictor_output: InternalLoadLevel) -> CognitiveWireState:
    """Map ML predictor output ('High'/'Medium'/'Low') to API wire state."""
    if predictor_output == "High":
        return "OVERLOAD"
    if predictor_output == "Low":
        return "LOW_LOAD"
    return "OPTIMAL"


def normalize_wire_state(raw: str) -> CognitiveWireState:
    """Normalize any incoming state string to a valid wire state."""
    upper = (raw or "").upper().strip()
    if upper in {"OVERLOAD", "HIGH_LOAD", "HIGH"}:
        return "OVERLOAD"
    if upper in {"LOW_LOAD", "UNDERLOAD", "LOW"}:
        return "LOW_LOAD"
    return "OPTIMAL"


def get_scene_duration(state: CognitiveWireState, text_length: int = 0) -> int:
    """
    Calculate scene duration in ms for a given cognitive state,
    scaled by text length so longer explanations get more time.
    """
    base = {
        "OVERLOAD": SCENE_DURATION_OVERLOAD,
        "OPTIMAL": SCENE_DURATION_OPTIMAL,
        "LOW_LOAD": SCENE_DURATION_LOW_LOAD,
    }.get(state, SCENE_DURATION_OPTIMAL)

    bonus = 0
    if text_length > 80:
        bonus = 500
    if text_length > 160:
        bonus = 1200

    return max(SCENE_DURATION_MIN, min(base + bonus, SCENE_DURATION_MAX))


def get_actor_limit(state: CognitiveWireState) -> int:
    """Return maximum number of actors for a given cognitive state."""
    return {
        "OVERLOAD": ACTOR_LIMIT_OVERLOAD,
        "OPTIMAL": ACTOR_LIMIT_OPTIMAL,
        "LOW_LOAD": ACTOR_LIMIT_LOW_LOAD,
    }.get(state, ACTOR_LIMIT_OPTIMAL)


def get_environment(state: CognitiveWireState) -> str:
    """Return background environment hint for a given cognitive state."""
    return {
        "OVERLOAD": ENVIRONMENT_OVERLOAD,
        "OPTIMAL": ENVIRONMENT_OPTIMAL,
        "LOW_LOAD": ENVIRONMENT_LOW_LOAD,
    }.get(state, ENVIRONMENT_OPTIMAL)


def get_ctml_principles(state: CognitiveWireState) -> list:
    """Return CTML principles applied for a given cognitive state."""
    return {
        "OVERLOAD": ["coherence", "signaling", "temporal_contiguity", "redundancy"],
        "OPTIMAL": ["segmenting", "signaling", "spatial_contiguity"],
        "LOW_LOAD": ["personalization", "generative_processing", "segmenting"],
    }.get(state, ["segmenting", "signaling"])


def get_salience_level(state: CognitiveWireState) -> str:
    """Return visual salience level for a given cognitive state."""
    return {
        "OVERLOAD": "low",
        "OPTIMAL": "medium",
        "LOW_LOAD": "high",
    }.get(state, "medium")
