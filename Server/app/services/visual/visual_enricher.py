"""
Visual Enricher - Adds Educational Visual Aids to Scenes

Enriches backend-generated scenes with domain-specific visual actors
based on keywords in the scene text, ensuring educationally-relevant
visuals are always present even when AI/hybrid generation is sparse.
"""
from typing import Any, Dict, List


def enrich_scene(scene_data: dict, concept_analysis: dict = None) -> dict:
    """
    Enrich a scene with educational visual aids. Returns enriched scene (copy).
    """
    concept_analysis = concept_analysis or {}
    scene_id = (scene_data.get("id") or "").lower()
    scene_text = (scene_data.get("text") or "").lower()
    actors = list(scene_data.get("actors") or [])
    domain = (concept_analysis.get("domain") or "generic").lower()
    topic = (concept_analysis.get("topic") or "").lower()

    # Photosynthesis (most specific - check first)
    if "photosynthesis" in topic or (domain == "biology" and any(kw in scene_text for kw in ["water", "carbon", "glucose", "oxygen", "sunlight", "chloro"])):
        actors = _enrich_photosynthesis(scene_id, scene_text, actors, domain)

    # Water cycle (check before general earth_science to prevent rock cycle from matching)
    elif ("water" in topic and "cycle" in topic) or any(kw in scene_text for kw in ["evaporation", "condensation", "precipitation", "runoff", "infiltration"]):
        actors = _enrich_water_cycle(scene_id, scene_text, actors, domain)

    # Rock cycle (check for specific rock cycle keywords)
    elif "rock cycle" in topic or any(kw in scene_text for kw in ["igneous", "sedimentary", "metamorphic", "magma", "lava", "erosion"]):
        actors = _enrich_rock_cycle(scene_id, scene_text, actors, domain)

    # General earth science
    elif domain == "earth_science" or "rock" in topic:
        actors = _enrich_rock_cycle(scene_id, scene_text, actors, domain)

    # Physics / mechanics
    elif domain == "physics" or any(kw in scene_text for kw in ["gravity", "force", "mass", "weight", "acceleration", "velocity", "orbit"]):
        actors = _enrich_physics(scene_id, scene_text, actors, domain)

    # Astronomy
    elif domain == "astronomy" or any(kw in scene_text for kw in ["planet", "orbit", "solar", "galaxy", "universe", "space"]):
        actors = _enrich_astronomy(scene_id, scene_text, actors, domain)

    # General visual aids always applied (non-destructive)
    actors = _add_general_visual_aids(scene_id, scene_text, actors, domain)

    out = scene_data.copy()
    out["actors"] = actors
    return out


def _enrich_photosynthesis(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Enrich photosynthesis scenes with roots, leaves, arrows, labels."""
    enriched = list(actors)
    has_plant = any(a.get("type") == "plant" for a in actors)
    has_root = any(a.get("type") == "root" for a in actors)
    has_leaf = any(a.get("type") == "leaf" for a in actors)

    # Ensure plant visual anchor
    if not has_plant:
        enriched.insert(0, {
            "type": "plant", "x": 400, "y": 350,
            "size": 40, "color": "#4CAF50", "animation": "grow",
        })
        has_plant = True

    if "water" in scene_text or "absorption" in scene_text or "root" in scene_text:
        if has_plant and not has_root:
            enriched.insert(0, {
                "type": "root", "x": 400, "y": 550,
                "depth": 80, "width": 100, "branches": 6,
                "color": "#8B4513", "animation": "absorb",
            })
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 400, "y": 520, "length": 120, "angle": -1.5708, "color": "#2196F3", "thickness": 2, "animation": "appear"})
        if not any(a.get("type") == "label" and (a.get("text") or "").strip() == "H₂O" for a in enriched):
            enriched.append({"type": "label", "x": 420, "y": 460, "text": "H₂O", "fontSize": 16, "color": "#2196F3", "animation": "appear"})

    if "carbon" in scene_text or "co2" in scene_text:
        if not any(a.get("type") == "label" and "CO₂" in str(a.get("text", "")) for a in enriched):
            enriched.append({"type": "label", "x": 520, "y": 250, "text": "CO₂", "fontSize": 16, "color": "#757575", "animation": "appear"})
        if has_plant and not has_leaf:
            enriched.append({"type": "leaf", "x": 400, "y": 200, "size": 35, "angle": 0, "color": "#4CAF50", "animation": "sway"})

    if "sun" in scene_text or "light" in scene_text or "chloro" in scene_text:
        if not any(a.get("type") == "sun" for a in enriched):
            enriched.append({"type": "sun", "x": 700, "y": 80, "size": 50, "rays": True, "color": "#FFD700", "animation": "shine"})
        if has_plant and not has_leaf:
            enriched.append({"type": "leaf", "x": 400, "y": 200, "size": 35, "angle": 0, "color": "#4CAF50", "animation": "sway"})
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 700, "y": 80, "length": 200, "angle": 0.785, "color": "#FFD700", "thickness": 3, "animation": "appear"})

    if "glucose" in scene_text or "sugar" in scene_text:
        if not any(a.get("type") == "glucose" for a in enriched):
            enriched.append({"type": "glucose", "x": 520, "y": 300, "size": 40, "color": "#FF9800", "animation": "appear"})
        if not any("C₆H₁₂O₆" in str(a.get("text", "")) for a in enriched if a.get("type") == "label"):
            enriched.append({"type": "label", "x": 520, "y": 350, "text": "C₆H₁₂O₆", "fontSize": 14, "color": "#FF9800", "animation": "appear"})

    if "oxygen" in scene_text or "o2" in scene_text:
        if not any("O₂" in str(a.get("text", "")) for a in enriched if a.get("type") == "label"):
            enriched.append({"type": "label", "x": 400, "y": 150, "text": "O₂", "fontSize": 16, "color": "#4CAF50", "animation": "appear"})

    return enriched


def _enrich_rock_cycle(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Enrich rock cycle / earth science scenes."""
    enriched = list(actors)

    if not any(a.get("type") == "mountain" for a in enriched):
        enriched.insert(0, {"type": "mountain", "x": 400, "y": 250, "size": 120, "color": "#795548", "animation": "idle"})

    if ("igneous" in scene_text or "magma" in scene_text or "lava" in scene_text) and not any(a.get("type") == "volcano" for a in enriched):
        enriched.append({"type": "volcano", "x": 600, "y": 350, "size": 80, "color": "#FF5722", "animation": "pulse"})

    if "erosion" in scene_text or "sediment" in scene_text:
        if not any(a.get("type") == "molecule" and a.get("moleculeType") == "sediment" for a in enriched):
            enriched.append({"type": "molecule", "x": 300, "y": 420, "moleculeType": "sediment", "size": 20, "color": "#9E9E9E", "animation": "moveDown"})
            enriched.append({"type": "label", "x": 300, "y": 460, "text": "Sediment", "fontSize": 13, "color": "#9E9E9E", "animation": "appear"})

    if "metamorphic" in scene_text or "pressure" in scene_text or "heat" in scene_text:
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 400, "y": 400, "length": 80, "angle": 1.5708, "color": "#FF5722", "thickness": 3, "animation": "pulse"})
            enriched.append({"type": "label", "x": 420, "y": 450, "text": "Heat + Pressure", "fontSize": 13, "color": "#FF5722", "animation": "appear"})

    return enriched


def _enrich_water_cycle(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Enrich water cycle scenes with appropriate actors."""
    enriched = list(actors)

    # Ensure sun is present in most water cycle scenes
    if not any(a.get("type") == "sun" for a in enriched):
        enriched.append({"type": "sun", "x": 700, "y": 80, "size": 50, "rays": True, "color": "#FFD700", "animation": "shine"})

    if "evaporation" in scene_text or "vapor" in scene_text or "steam" in scene_text:
        if not any(a.get("type") == "ocean" for a in enriched):
            enriched.insert(0, {"type": "ocean", "x": 400, "y": 450, "size": 200, "color": "#2196F3", "animation": "wave"})
        if not any(a.get("type") == "molecule" for a in enriched):
            for i, x in enumerate([350, 400, 450]):
                enriched.append({"type": "molecule", "x": x, "y": 420, "moleculeType": "water", "size": 18, "animation": "bubbleUp"})
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 400, "y": 350, "length": 150, "angle": -1.5708, "color": "#FF9800", "animation": "appear"})
        if not any(a.get("type") == "label" and "Water Vapor" in str(a.get("text", "")) for a in enriched):
            enriched.append({"type": "label", "x": 420, "y": 290, "text": "Water Vapor ↑", "fontSize": 14, "color": "#FF9800", "animation": "appear"})

    if "condensation" in scene_text or "cloud" in scene_text or "cool" in scene_text:
        if not any(a.get("type") == "cloud" for a in enriched):
            enriched.append({"type": "cloud", "x": 400, "y": 150, "size": 60, "animation": "grow"})

    if "precipitation" in scene_text or "rain" in scene_text or "snow" in scene_text:
        if not any(a.get("type") == "cloud" for a in enriched):
            enriched.append({"type": "cloud", "x": 400, "y": 150, "size": 60, "animation": "sway"})
        if not any(a.get("type") == "molecule" for a in enriched):
            for i, x in enumerate([380, 400, 420]):
                enriched.append({"type": "molecule", "x": x, "y": 200, "moleculeType": "water", "size": 22, "animation": "fall"})
        if not any(a.get("type") == "label" and "Rain" in str(a.get("text", "")) for a in enriched):
            enriched.append({"type": "label", "x": 420, "y": 420, "text": "Rain ↓", "fontSize": 16, "color": "#2196F3", "animation": "appear"})

    if "runoff" in scene_text or "river" in scene_text or "stream" in scene_text:
        if not any(a.get("type") == "mountain" for a in enriched):
            enriched.append({"type": "mountain", "x": 200, "y": 300, "size": 100, "color": "#795548", "animation": "idle"})
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 300, "y": 350, "length": 150, "angle": 0.5, "color": "#2196F3", "animation": "appear"})

    if "groundwater" in scene_text or "infiltration" in scene_text or "soil" in scene_text:
        if not any(a.get("type") == "plant" for a in enriched):
            enriched.append({"type": "plant", "x": 500, "y": 350, "size": 40, "color": "#4CAF50", "animation": "grow"})
        if not any(a.get("type") == "label" and "Groundwater" in str(a.get("text", "")) for a in enriched):
            enriched.append({"type": "label", "x": 470, "y": 430, "text": "Groundwater", "fontSize": 14, "color": "#8B4513", "animation": "appear"})

    return enriched


def _enrich_physics(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Enrich physics scenes (gravity, force, motion)."""
    enriched = list(actors)

    if "gravity" in scene_text or "fall" in scene_text or "pull" in scene_text:
        if not any(a.get("type") == "earth" for a in enriched):
            enriched.insert(0, {"type": "earth", "x": 400, "y": 450, "size": 60, "color": "#4A90E2", "animation": "idle"})
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 400, "y": 220, "length": 150, "angle": 1.5708, "color": "#1D4ED8", "thickness": 3, "animation": "appear"})
        if not any(a.get("type") == "label" and "Gravity" in str(a.get("text", "")) for a in enriched):
            enriched.append({"type": "label", "x": 430, "y": 300, "text": "Gravity ↓", "fontSize": 14, "color": "#1D4ED8", "animation": "appear"})

    if "orbit" in scene_text or "revolution" in scene_text:
        if not any(a.get("type") in ["earth", "planet"] for a in enriched):
            enriched.insert(0, {"type": "earth", "x": 400, "y": 400, "size": 60, "color": "#4A90E2", "animation": "idle"})
        if not any(a.get("type") in ["moon", "planet"] for a in enriched):
            enriched.append({"type": "moon", "x": 600, "y": 200, "size": 30, "color": "#E0E0E0", "animation": "rotate"})
        if not any(a.get("type") == "arrow" for a in enriched):
            enriched.append({"type": "arrow", "x": 500, "y": 300, "length": 100, "angle": -0.785, "color": "#9E9E9E", "thickness": 2, "animation": "appear"})

    if "force" in scene_text and not any(a.get("type") == "number" for a in enriched):
        enriched.append({"type": "number", "x": 400, "y": 200, "text": "F = ma", "fontSize": 18, "color": "#FF5722", "animation": "pulse"})

    if "mass" in scene_text or "weight" in scene_text:
        if not any(a.get("type") == "label" and "mass" in str(a.get("text", "")).lower() for a in enriched):
            enriched.append({"type": "label", "x": 400, "y": 160, "text": "Mass = m", "fontSize": 14, "color": "#795548", "animation": "appear"})

    return enriched


def _enrich_astronomy(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Enrich astronomy scenes."""
    enriched = list(actors)

    if not any(a.get("type") == "sun" for a in enriched) and ("sun" in scene_text or "solar" in scene_text or "star" in scene_text):
        enriched.insert(0, {"type": "sun", "x": 100, "y": 300, "size": 60, "rays": True, "color": "#FFD700", "animation": "shine"})

    if ("orbit" in scene_text or "revolve" in scene_text) and not any(a.get("type") in ["planet", "earth", "moon"] for a in enriched):
        enriched.append({"type": "planet", "x": 400, "y": 300, "size": 50, "color": "#42A5F5", "animation": "rotate"})

    if "galaxy" in scene_text or "universe" in scene_text:
        for i, (x, y) in enumerate([(150, 100), (600, 150), (700, 400)]):
            if not any(a.get("type") == "star" and a.get("x") == x for a in enriched):
                enriched.append({"type": "star", "x": x, "y": y, "size": 15, "color": "#FFD700", "animation": "shine"})

    return enriched


def _add_general_visual_aids(scene_id: str, scene_text: str, actors: list, domain: str) -> list:
    """Add general visual aids based on keywords. Non-destructive — only adds missing elements."""
    enriched = list(actors)
    has_label = any(a.get("type") == "label" for a in enriched)
    has_arrow = any(a.get("type") == "arrow" for a in enriched)

    # Add directional arrows for motion/flow keywords
    if not has_arrow and any(kw in scene_text for kw in ["direction", "toward", "flow", "move", "travel", "transfer"]):
        enriched.append({"type": "arrow", "x": 400, "y": 300, "length": 120, "angle": 0, "color": "#FF5722", "thickness": 2, "animation": "appear"})

    # Add equation labels for math/formula keywords
    if any(kw in scene_text for kw in ["formula", "equation", "calculate", "equals"]) and not has_label:
        enriched.append({"type": "label", "x": 400, "y": 200, "text": "Formula", "fontSize": 16, "color": "#1565C0", "animation": "appear"})

    # Add increase/decrease indicator
    if any(kw in scene_text for kw in ["increase", "rises", "grows", "increases"]) and not has_arrow:
        enriched.append({"type": "arrow", "x": 400, "y": 350, "length": 100, "angle": -1.5708, "color": "#4CAF50", "thickness": 2, "animation": "appear"})
    elif any(kw in scene_text for kw in ["decrease", "falls", "drops", "decreases"]) and not has_arrow:
        enriched.append({"type": "arrow", "x": 400, "y": 250, "length": 100, "angle": 1.5708, "color": "#F44336", "thickness": 2, "animation": "appear"})

    return enriched
