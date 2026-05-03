"""
Prebuilt high-quality animation scripts.

These are hand-crafted "gold standard" scripts used as:
  1. Direct return for well-known concepts (zero latency)
  2. Few-shot exemplars injected into Gemini prompts (quality anchor)

Each script follows the AnimationEngine contract:
  - All actors have: type, x, y, size, color, animation
  - startTime accumulated correctly
  - Scenes tell a visual story with cause → effect logic
  - Animations are purposeful (motion has meaning)
"""

from typing import Dict, Any, Optional

# ─── WATER CYCLE ─────────────────────────────────────────────────────────────

WATER_CYCLE_SCRIPT: Dict[str, Any] = {
    "title": "The Water Cycle: Earth's Endless Journey of Water",
    "duration": 45000,
    "scenes": [
        {
            "id": "intro",
            "startTime": 0,
            "duration": 5000,
            "text": "The Water Cycle: Water moves from oceans to sky and back again, giving us rain and rivers.",
            "actors": [
                {"type": "ocean", "x": 400, "y": 450, "size": 200, "color": "#2196F3", "animation": "wave"},
                {"type": "cloud", "x": 400, "y": 150, "size": 60, "animation": "appear"},
                {"type": "sun",   "x": 680, "y": 80,  "size": 50,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "label", "x": 400, "y": 500, "text": "Ocean", "fontSize": 16, "color": "#1976D2", "animation": "appear"},
                {"type": "label", "x": 400, "y": 100, "text": "Clouds", "fontSize": 16, "color": "#607D8B", "animation": "appear"},
            ],
        },
        {
            "id": "evaporation",
            "startTime": 5000,
            "duration": 7000,
            "text": "Step 1: Evaporation — The sun heats the ocean surface. Water molecules gain energy and escape as invisible water vapour, rising upward.",
            "actors": [
                {"type": "ocean",    "x": 400,  "y": 450, "size": 200, "color": "#2196F3",  "animation": "wave"},
                {"type": "sun",      "x": 680,  "y": 80,  "size": 55,  "color": "#FFD700",  "animation": "shine", "rays": True},
                {"type": "molecule", "x": 330,  "y": 420, "moleculeType": "water", "size": 22, "color": "#29B6F6", "animation": "bubbleUp"},
                {"type": "molecule", "x": 390,  "y": 430, "moleculeType": "water", "size": 22, "color": "#29B6F6", "animation": "bubbleUp"},
                {"type": "molecule", "x": 450,  "y": 410, "moleculeType": "water", "size": 22, "color": "#29B6F6", "animation": "bubbleUp"},
                {"type": "arrow",    "x": 680,  "y": 120, "length": 200, "angle": 2.5, "color": "#FFA726", "thickness": 3, "animation": "appear"},
                {"type": "arrow",    "x": 400,  "y": 360, "length": 160, "angle": -1.5708, "color": "#FF9800", "thickness": 2, "animation": "appear"},
                {"type": "label",    "x": 420,  "y": 310, "text": "Water Vapour ↑", "fontSize": 14, "color": "#E65100", "animation": "appear"},
            ],
        },
        {
            "id": "condensation",
            "startTime": 12000,
            "duration": 7000,
            "text": "Step 2: Condensation — Rising vapour cools at high altitude. Cool molecules slow down and cluster together forming tiny cloud droplets.",
            "actors": [
                {"type": "ocean",    "x": 400,  "y": 450, "size": 200, "color": "#2196F3", "animation": "wave"},
                {"type": "sun",      "x": 680,  "y": 80,  "size": 50,  "color": "#FFD700", "animation": "shine"},
                {"type": "molecule", "x": 370,  "y": 280, "moleculeType": "water", "size": 16, "color": "#90CAF9", "animation": "vibrate"},
                {"type": "molecule", "x": 400,  "y": 260, "moleculeType": "water", "size": 16, "color": "#90CAF9", "animation": "vibrate"},
                {"type": "molecule", "x": 430,  "y": 275, "moleculeType": "water", "size": 16, "color": "#90CAF9", "animation": "vibrate"},
                {"type": "cloud",    "x": 400,  "y": 160, "size": 65,  "color": "#ECEFF1", "animation": "grow"},
                {"type": "arrow",    "x": 400,  "y": 260, "length": 80, "angle": -1.5708, "color": "#78909C", "thickness": 2, "animation": "appear"},
                {"type": "label",    "x": 480,  "y": 185, "text": "Droplets cluster → Cloud", "fontSize": 13, "color": "#455A64", "animation": "appear"},
            ],
        },
        {
            "id": "precipitation",
            "startTime": 19000,
            "duration": 7000,
            "text": "Step 3: Precipitation — Clouds grow heavy. When droplets are too large to stay suspended, they fall as rain, snow or hail.",
            "actors": [
                {"type": "ocean",    "x": 400,  "y": 450, "size": 200, "color": "#2196F3", "animation": "wave"},
                {"type": "cloud",    "x": 400,  "y": 150, "size": 70,  "color": "#B0BEC5", "animation": "sway"},
                {"type": "molecule", "x": 370,  "y": 210, "moleculeType": "water", "size": 26, "color": "#1E88E5", "animation": "fall"},
                {"type": "molecule", "x": 400,  "y": 200, "moleculeType": "water", "size": 26, "color": "#1E88E5", "animation": "fall"},
                {"type": "molecule", "x": 430,  "y": 215, "moleculeType": "water", "size": 26, "color": "#1E88E5", "animation": "fall"},
                {"type": "arrow",    "x": 400,  "y": 230, "length": 200, "angle": 1.5708, "color": "#1976D2", "thickness": 4, "animation": "appear"},
                {"type": "label",    "x": 450,  "y": 380, "text": "Rain ↓", "fontSize": 17, "color": "#1565C0", "animation": "appear"},
            ],
        },
        {
            "id": "runoff",
            "startTime": 26000,
            "duration": 6000,
            "text": "Step 4: Surface Runoff — Rainwater flows downhill along the surface, forming streams and rivers that carry water back to the ocean.",
            "actors": [
                {"type": "ocean",    "x": 500,  "y": 450, "size": 200, "color": "#2196F3", "animation": "wave"},
                {"type": "mountain", "x": 200,  "y": 310, "size": 110, "color": "#795548", "animation": "idle"},
                {"type": "molecule", "x": 280,  "y": 380, "moleculeType": "water", "size": 22, "color": "#42A5F5", "animation": "moveDown"},
                {"type": "molecule", "x": 340,  "y": 400, "moleculeType": "water", "size": 22, "color": "#42A5F5", "animation": "moveDown"},
                {"type": "arrow",    "x": 250,  "y": 380, "length": 240, "angle": 0.45, "color": "#1976D2", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 380,  "y": 430, "text": "River → back to Ocean", "fontSize": 14, "color": "#1565C0", "animation": "appear"},
            ],
        },
        {
            "id": "infiltration",
            "startTime": 32000,
            "duration": 6000,
            "text": "Step 5: Infiltration — Some rainwater seeps into soil, becoming groundwater. Roots absorb it; some reaches deep aquifers that store fresh water.",
            "actors": [
                {"type": "plant",    "x": 470,  "y": 340, "size": 46,  "color": "#388E3C", "animation": "grow"},
                {"type": "root",     "x": 470,  "y": 480, "size": 55,  "color": "#6D4C41", "animation": "absorb"},
                {"type": "molecule", "x": 380,  "y": 460, "moleculeType": "water", "size": 20, "color": "#42A5F5", "animation": "moveDown"},
                {"type": "molecule", "x": 430,  "y": 450, "moleculeType": "water", "size": 20, "color": "#42A5F5", "animation": "absorb"},
                {"type": "arrow",    "x": 420,  "y": 430, "length": 80, "angle": 1.5708, "color": "#5D4037", "thickness": 2, "animation": "appear"},
                {"type": "label",    "x": 560,  "y": 460, "text": "Groundwater", "fontSize": 14, "color": "#4E342E", "animation": "appear"},
                {"type": "label",    "x": 510,  "y": 310, "text": "Roots absorb water", "fontSize": 13, "color": "#2E7D32", "animation": "appear"},
            ],
        },
        {
            "id": "summary",
            "startTime": 38000,
            "duration": 7000,
            "text": "The cycle never stops! Evaporation → Condensation → Precipitation → Runoff → Infiltration → back to Evaporation. Water is constantly recycled.",
            "actors": [
                {"type": "ocean",    "x": 400,  "y": 453, "size": 200, "color": "#2196F3", "animation": "wave"},
                {"type": "sun",      "x": 680,  "y": 80,  "size": 55,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "cloud",    "x": 350,  "y": 145, "size": 60,  "color": "#B0BEC5", "animation": "sway"},
                {"type": "mountain", "x": 180,  "y": 310, "size": 100, "color": "#795548", "animation": "idle"},
                {"type": "plant",    "x": 520,  "y": 340, "size": 40,  "color": "#4CAF50", "animation": "sway"},
                {"type": "arrow",    "x": 400,  "y": 380, "length": 200, "angle": -1.5708, "color": "#FF9800", "thickness": 2, "animation": "appear"},
                {"type": "arrow",    "x": 400,  "y": 200, "length": 200, "angle": 1.5708, "color": "#1976D2", "thickness": 2, "animation": "appear"},
                {"type": "label",    "x": 400,  "y": 560, "text": "The Endless Water Cycle", "fontSize": 16, "color": "#0D47A1", "animation": "appear"},
            ],
        },
    ],
}

# ─── PHOTOSYNTHESIS ───────────────────────────────────────────────────────────

PHOTOSYNTHESIS_SCRIPT: Dict[str, Any] = {
    "title": "Photosynthesis: How Plants Make Food from Sunlight",
    "duration": 51000,
    "scenes": [
        {
            "id": "intro",
            "startTime": 0,
            "duration": 6000,
            "text": "Plants are nature's solar-powered food factories. They capture sunlight and convert air and water into sugar. This is photosynthesis.",
            "actors": [
                {"type": "plant",  "x": 380, "y": 350, "size": 90,  "color": "#2E7D32", "animation": "grow"},
                {"type": "sun",    "x": 680, "y": 80,  "size": 58,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "label",  "x": 390, "y": 530, "text": "Green Plant",       "fontSize": 15, "color": "#2E7D32", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 145, "text": "Photosynthesis",    "fontSize": 19, "color": "#F57F17", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 175, "text": "Sunlight + CO₂ + H₂O → Glucose + O₂", "fontSize": 12, "color": "#BF360C", "animation": "appear"},
            ],
        },
        {
            "id": "sunlight_absorbed",
            "startTime": 6000,
            "duration": 8000,
            "text": "Step 1 — Light Absorption: Chlorophyll inside leaf cells absorbs red and blue sunlight. This captured energy will drive the whole process.",
            "actors": [
                {"type": "sun",   "x": 680, "y": 80,  "size": 55,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "plant", "x": 380, "y": 360, "size": 82,  "color": "#2E7D32", "animation": "sway"},
                {"type": "leaf",  "x": 380, "y": 228, "size": 48,  "color": "#43A047", "animation": "glow"},
                {"type": "bolt",  "x": 415, "y": 220, "size": 32,  "color": "#FFEE58", "animation": "pulse"},
                {"type": "arrow", "x": 620, "y": 115, "length": 195, "angle": 2.45, "color": "#FFA726", "thickness": 3, "animation": "appear"},
                {"type": "label", "x": 310, "y": 185, "text": "Chlorophyll absorbs light", "fontSize": 13, "color": "#558B2F", "animation": "appear"},
                {"type": "label", "x": 440, "y": 195, "text": "⚡ Light Energy", "fontSize": 13, "color": "#F9A825", "animation": "appear"},
            ],
        },
        {
            "id": "water_absorbed",
            "startTime": 14000,
            "duration": 8000,
            "text": "Step 2 — Water Uptake: Roots absorb water (H₂O) from the soil. Water travels up the stem to the leaves through tiny tubes called xylem.",
            "actors": [
                {"type": "plant",    "x": 380, "y": 345, "size": 82,  "color": "#2E7D32", "animation": "idle"},
                {"type": "root",     "x": 380, "y": 490, "size": 62,  "color": "#795548", "animation": "absorb"},
                {"type": "molecule", "x": 250, "y": 490, "moleculeType": "water", "size": 23, "color": "#29B6F6", "animation": "moveUp"},
                {"type": "molecule", "x": 300, "y": 500, "moleculeType": "water", "size": 23, "color": "#29B6F6", "animation": "moveUp"},
                {"type": "molecule", "x": 340, "y": 485, "moleculeType": "water", "size": 23, "color": "#29B6F6", "animation": "moveUp"},
                {"type": "arrow",    "x": 380, "y": 455, "length": 130, "angle": -1.5708, "color": "#0288D1", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 210, "y": 530, "text": "H₂O from soil", "fontSize": 14, "color": "#0277BD", "animation": "appear"},
                {"type": "label",    "x": 480, "y": 400, "text": "Xylem carries water up", "fontSize": 13, "color": "#4E342E", "animation": "appear"},
            ],
        },
        {
            "id": "co2_enters",
            "startTime": 22000,
            "duration": 8000,
            "text": "Step 3 — CO₂ Enters: Carbon dioxide from the air enters the leaf through microscopic pores called stomata on the underside of leaves.",
            "actors": [
                {"type": "plant",    "x": 380, "y": 350, "size": 82,  "color": "#2E7D32", "animation": "idle"},
                {"type": "leaf",     "x": 380, "y": 228, "size": 46,  "color": "#43A047", "animation": "sway"},
                {"type": "molecule", "x": 570, "y": 240, "moleculeType": "co2", "size": 28, "color": "#78909C", "animation": "floatIn"},
                {"type": "molecule", "x": 610, "y": 200, "moleculeType": "co2", "size": 28, "color": "#78909C", "animation": "floatIn"},
                {"type": "arrow",    "x": 540, "y": 235, "length": 135, "angle": 3.14159, "color": "#607D8B", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 430, "y": 160, "text": "Stomata (tiny pores)", "fontSize": 13, "color": "#37474F", "animation": "appear"},
                {"type": "label",    "x": 580, "y": 285, "text": "CO₂ enters leaf", "fontSize": 13, "color": "#546E7A", "animation": "appear"},
            ],
        },
        {
            "id": "light_reactions",
            "startTime": 30000,
            "duration": 7000,
            "text": "Step 4 — Light Reactions: Inside the chloroplast, light energy splits water molecules. This releases oxygen and creates energy carriers (ATP).",
            "actors": [
                {"type": "leaf",     "x": 380, "y": 270, "size": 60,  "color": "#66BB6A", "animation": "glow"},
                {"type": "bolt",     "x": 350, "y": 270, "size": 38,  "color": "#FFEE58", "animation": "pulse"},
                {"type": "molecule", "x": 450, "y": 280, "moleculeType": "water", "size": 25, "color": "#29B6F6", "animation": "vibrate"},
                {"type": "molecule", "x": 540, "y": 240, "moleculeType": "o2",    "size": 26, "color": "#66BB6A", "animation": "floatOut"},
                {"type": "arrow",    "x": 420, "y": 265, "length": 100, "angle": -0.4, "color": "#26A69A", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 380, "y": 195, "text": "H₂O split by light → O₂ released", "fontSize": 13, "color": "#00695C", "animation": "appear"},
                {"type": "label",    "x": 570, "y": 210, "text": "O₂ →", "fontSize": 16, "color": "#2E7D32", "animation": "appear"},
            ],
        },
        {
            "id": "glucose_made",
            "startTime": 37000,
            "duration": 8000,
            "text": "Step 5 — Calvin Cycle: CO₂ molecules are assembled into glucose (C₆H₁₂O₆) using the captured light energy. Glucose fuels the plant's growth.",
            "actors": [
                {"type": "plant",    "x": 360, "y": 340, "size": 82,  "color": "#388E3C", "animation": "grow"},
                {"type": "leaf",     "x": 360, "y": 215, "size": 48,  "color": "#66BB6A", "animation": "glow"},
                {"type": "bolt",     "x": 350, "y": 250, "size": 36,  "color": "#FFEE58", "animation": "pulse"},
                {"type": "molecule", "x": 530, "y": 260, "moleculeType": "co2", "size": 24, "color": "#90A4AE", "animation": "floatIn"},
                {"type": "glucose",  "x": 530, "y": 310, "size": 44,  "color": "#FF9800", "animation": "appear"},
                {"type": "arrow",    "x": 440, "y": 285, "length": 70, "angle": 0, "color": "#FF6F00", "thickness": 4, "animation": "appear"},
                {"type": "label",    "x": 530, "y": 365, "text": "Glucose C₆H₁₂O₆", "fontSize": 14, "color": "#E65100", "animation": "appear"},
                {"type": "label",    "x": 240, "y": 250, "text": "Light energy drives assembly", "fontSize": 13, "color": "#F9A825", "animation": "appear"},
            ],
        },
        {
            "id": "summary",
            "startTime": 45000,
            "duration": 6000,
            "text": "Summary: 6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂. Sunlight powers everything — without photosynthesis, almost no life could exist on Earth.",
            "actors": [
                {"type": "sun",      "x": 670, "y": 75,  "size": 55,  "color": "#FFD700",  "animation": "shine", "rays": True},
                {"type": "plant",    "x": 350, "y": 340, "size": 84,  "color": "#2E7D32",  "animation": "sway"},
                {"type": "root",     "x": 350, "y": 490, "size": 55,  "color": "#795548",  "animation": "idle"},
                {"type": "molecule", "x": 200, "y": 490, "moleculeType": "water", "size": 22, "color": "#29B6F6", "animation": "moveUp"},
                {"type": "molecule", "x": 575, "y": 195, "moleculeType": "co2",   "size": 25, "color": "#90A4AE", "animation": "floatIn"},
                {"type": "glucose",  "x": 530, "y": 300, "size": 40,  "color": "#FF9800",  "animation": "pulse"},
                {"type": "molecule", "x": 560, "y": 140, "moleculeType": "o2",    "size": 25, "color": "#4CAF50", "animation": "floatOut"},
                {"type": "label",    "x": 400, "y": 570, "text": "6CO₂ + 6H₂O + Light → Glucose + O₂", "fontSize": 13, "color": "#1A237E", "animation": "appear"},
            ],
        },
    ],
}

# ─── GRAVITY ─────────────────────────────────────────────────────────────────

GRAVITY_SCRIPT: Dict[str, Any] = {
    "title": "Gravity: The Force That Holds the Universe Together",
    "duration": 44000,
    "scenes": [
        {
            "id": "intro",
            "startTime": 0,
            "duration": 6000,
            "text": "Gravity is an invisible pulling force between all objects that have mass. The more mass an object has, the stronger its gravitational pull.",
            "actors": [
                {"type": "planet", "x": 400, "y": 405, "size": 105, "color": "#4A90E2", "animation": "idle"},
                {"type": "rock",   "x": 400, "y": 170, "size": 32,  "color": "#78909C", "animation": "idle"},
                {"type": "arrow",  "x": 400, "y": 205, "length": 155, "angle": 1.5708, "color": "#EF5350", "thickness": 4, "animation": "pulse"},
                {"type": "label",  "x": 475, "y": 280, "text": "Gravity pulls down",  "fontSize": 15, "color": "#C62828", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 130, "text": "All objects fall toward Earth", "fontSize": 14, "color": "#37474F", "animation": "appear"},
            ],
        },
        {
            "id": "same_acceleration",
            "startTime": 6000,
            "duration": 8000,
            "text": "Step 1 — Equal Acceleration: All objects fall at the same rate regardless of mass. Gravity gives every object the same acceleration: g = 9.8 m/s² downward.",
            "actors": [
                {"type": "planet", "x": 400, "y": 435, "size": 105, "color": "#4A90E2", "animation": "idle"},
                {"type": "rock",   "x": 290, "y": 175, "size": 44,  "color": "#616161", "animation": "fall"},
                {"type": "rock",   "x": 510, "y": 175, "size": 18,  "color": "#9E9E9E", "animation": "fall"},
                {"type": "arrow",  "x": 290, "y": 210, "length": 90, "angle": 1.5708, "color": "#EF5350", "thickness": 4, "animation": "appear"},
                {"type": "arrow",  "x": 510, "y": 210, "length": 90, "angle": 1.5708, "color": "#EF5350", "thickness": 4, "animation": "appear"},
                {"type": "label",  "x": 290, "y": 143, "text": "Heavy",  "fontSize": 14, "color": "#424242", "animation": "appear"},
                {"type": "label",  "x": 510, "y": 143, "text": "Light",  "fontSize": 14, "color": "#424242", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 110, "text": "Both fall at g = 9.8 m/s²", "fontSize": 14, "color": "#6A1B9A", "animation": "appear"},
            ],
        },
        {
            "id": "orbit_moon",
            "startTime": 14000,
            "duration": 8000,
            "text": "Step 2 — Orbital Motion: The Moon is constantly falling toward Earth but its sideways speed keeps it in orbit. Gravity and velocity balance perfectly.",
            "actors": [
                {"type": "planet", "x": 370, "y": 300, "size": 94,  "color": "#4A90E2", "animation": "idle"},
                {"type": "moon",   "x": 610, "y": 195, "size": 38,  "color": "#CFD8DC", "animation": "rotate"},
                {"type": "arrow",  "x": 570, "y": 225, "length": 90, "angle": -2.356, "color": "#1565C0", "thickness": 3, "animation": "pulse"},
                {"type": "arrow",  "x": 610, "y": 200, "length": 80, "angle": -1.5708, "color": "#F9A825", "thickness": 2, "animation": "appear"},
                {"type": "label",  "x": 390, "y": 190, "text": "Earth",  "fontSize": 14, "color": "#1565C0", "animation": "appear"},
                {"type": "label",  "x": 650, "y": 165, "text": "Moon",   "fontSize": 14, "color": "#455A64", "animation": "appear"},
                {"type": "label",  "x": 620, "y": 285, "text": "← Gravity pull",    "fontSize": 13, "color": "#1565C0", "animation": "appear"},
                {"type": "label",  "x": 640, "y": 155, "text": "↑ Sideways velocity", "fontSize": 12, "color": "#F57F17", "animation": "appear"},
            ],
        },
        {
            "id": "universal_gravity",
            "startTime": 22000,
            "duration": 8000,
            "text": "Step 3 — Universal Law: Every mass attracts every other mass. Bigger mass = stronger pull. Greater distance = weaker pull. F = G × m₁ × m₂ / r²",
            "actors": [
                {"type": "sun",    "x": 160, "y": 305, "size": 72,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "planet", "x": 400, "y": 305, "size": 60,  "color": "#29B6F6", "animation": "rotate"},
                {"type": "planet", "x": 598, "y": 305, "size": 40,  "color": "#AB47BC", "animation": "rotate"},
                {"type": "arrow",  "x": 220, "y": 305, "length": 135, "angle": 0, "color": "#FF8F00", "thickness": 5, "animation": "pulse"},
                {"type": "arrow",  "x": 450, "y": 305, "length": 110, "angle": 0, "color": "#FF8F00", "thickness": 3, "animation": "pulse"},
                {"type": "label",  "x": 400, "y": 205, "text": "Bigger mass = stronger gravity", "fontSize": 13, "color": "#E65100", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 415, "text": "F = G m₁m₂ / r²",  "fontSize": 14, "color": "#4A148C", "animation": "appear"},
            ],
        },
        {
            "id": "weight_vs_mass",
            "startTime": 30000,
            "duration": 7000,
            "text": "Step 4 — Weight vs Mass: Mass is the amount of matter; it never changes. Weight is the gravitational force on that mass — it changes on different planets!",
            "actors": [
                {"type": "planet", "x": 230, "y": 400, "size": 65,  "color": "#4A90E2", "animation": "idle"},
                {"type": "planet", "x": 570, "y": 400, "size": 30,  "color": "#EF9A9A", "animation": "idle"},
                {"type": "rock",   "x": 230, "y": 295, "size": 32,  "color": "#78909C", "animation": "fall"},
                {"type": "rock",   "x": 570, "y": 295, "size": 32,  "color": "#78909C", "animation": "fall"},
                {"type": "label",  "x": 230, "y": 210, "text": "Earth — g = 9.8 m/s²",  "fontSize": 13, "color": "#1565C0", "animation": "appear"},
                {"type": "label",  "x": 570, "y": 210, "text": "Moon — g = 1.6 m/s²",   "fontSize": 13, "color": "#7B1FA2", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 155, "text": "Same mass, different weight!", "fontSize": 15, "color": "#880E4F", "animation": "appear"},
            ],
        },
        {
            "id": "summary",
            "startTime": 37000,
            "duration": 7000,
            "text": "Summary: Gravity pulls every mass toward every other mass. It holds us on Earth, keeps the Moon in orbit, and holds the solar system together.",
            "actors": [
                {"type": "sun",    "x": 120, "y": 300, "size": 68,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "planet", "x": 380, "y": 300, "size": 82,  "color": "#4A90E2", "animation": "rotate"},
                {"type": "moon",   "x": 570, "y": 210, "size": 34,  "color": "#CFD8DC", "animation": "rotate"},
                {"type": "rock",   "x": 380, "y": 215, "size": 22,  "color": "#78909C", "animation": "fall"},
                {"type": "arrow",  "x": 180, "y": 300, "length": 160, "angle": 0, "color": "#FF8F00", "thickness": 3, "animation": "appear"},
                {"type": "arrow",  "x": 530, "y": 250, "length": 80, "angle": -2.356, "color": "#1565C0", "thickness": 2, "animation": "appear"},
                {"type": "label",  "x": 400, "y": 555, "text": "Gravity: F = G × m₁ × m₂ / r²", "fontSize": 14, "color": "#311B92", "animation": "appear"},
            ],
        },
    ],
}

# ─── SOLAR SYSTEM ─────────────────────────────────────────────────────────────

SOLAR_SYSTEM_SCRIPT: Dict[str, Any] = {
    "title": "The Solar System: Our Cosmic Neighbourhood",
    "duration": 40000,
    "scenes": [
        {
            "id": "intro",
            "startTime": 0,
            "duration": 6000,
            "text": "Our Solar System is made of the Sun and everything bound to it by gravity — 8 planets, moons, asteroids, and comets.",
            "actors": [
                {"type": "sun",    "x": 400, "y": 300, "size": 80,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "planet", "x": 260, "y": 300, "size": 22,  "color": "#9E9E9E", "animation": "rotate"},
                {"type": "planet", "x": 320, "y": 300, "size": 30,  "color": "#C8A951", "animation": "rotate"},
                {"type": "planet", "x": 500, "y": 300, "size": 35,  "color": "#4A90E2", "animation": "rotate"},
                {"type": "planet", "x": 580, "y": 300, "size": 28,  "color": "#D2553A", "animation": "rotate"},
                {"type": "label",  "x": 400, "y": 240, "text": "The Sun",          "fontSize": 16, "color": "#F57F17", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 550, "text": "Our Solar System", "fontSize": 18, "color": "#1A237E", "animation": "appear"},
            ],
        },
        {
            "id": "the_sun",
            "startTime": 6000,
            "duration": 7000,
            "text": "Step 1 — The Sun: The Sun is a giant ball of hot plasma 1.4 million km wide. It produces energy by nuclear fusion, turning hydrogen into helium.",
            "actors": [
                {"type": "sun",   "x": 400, "y": 300, "size": 120, "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "bolt",  "x": 400, "y": 300, "size": 50,  "color": "#FFF176", "animation": "pulse"},
                {"type": "label", "x": 400, "y": 165, "text": "The Sun: 99.8% of Solar System's mass", "fontSize": 13, "color": "#E65100", "animation": "appear"},
                {"type": "label", "x": 400, "y": 450, "text": "H + H → He + Energy (Fusion)", "fontSize": 14, "color": "#BF360C", "animation": "appear"},
                {"type": "arrow", "x": 520, "y": 300, "length": 90, "angle": 0.4, "color": "#FFA726", "thickness": 3, "animation": "appear"},
                {"type": "label", "x": 590, "y": 265, "text": "Light & Heat →", "fontSize": 13, "color": "#FF8F00", "animation": "appear"},
            ],
        },
        {
            "id": "inner_planets",
            "startTime": 13000,
            "duration": 7000,
            "text": "Step 2 — Inner Planets: Mercury, Venus, Earth, Mars are small rocky planets close to the Sun. Earth is in the habitable zone — just right for liquid water.",
            "actors": [
                {"type": "sun",    "x": 130, "y": 300, "size": 60,  "color": "#FFD700", "animation": "shine"},
                {"type": "planet", "x": 240, "y": 300, "size": 18,  "color": "#9E9E9E", "animation": "rotate"},
                {"type": "planet", "x": 310, "y": 300, "size": 26,  "color": "#E8D44D", "animation": "rotate"},
                {"type": "planet", "x": 400, "y": 300, "size": 32,  "color": "#4A90E2", "animation": "rotate"},
                {"type": "planet", "x": 490, "y": 300, "size": 24,  "color": "#D2553A", "animation": "rotate"},
                {"type": "label",  "x": 240, "y": 260, "text": "Mercury", "fontSize": 11, "color": "#616161", "animation": "appear"},
                {"type": "label",  "x": 310, "y": 260, "text": "Venus",   "fontSize": 11, "color": "#C9B429", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 255, "text": "Earth ✓", "fontSize": 12, "color": "#1565C0", "animation": "appear"},
                {"type": "label",  "x": 490, "y": 260, "text": "Mars",    "fontSize": 11, "color": "#B71C1C", "animation": "appear"},
            ],
        },
        {
            "id": "outer_planets",
            "startTime": 20000,
            "duration": 8000,
            "text": "Step 3 — Outer Planets: Jupiter, Saturn, Uranus, Neptune are gas and ice giants much larger than Earth. Jupiter alone is 1,300 times Earth's volume.",
            "actors": [
                {"type": "sun",    "x": 130, "y": 300, "size": 50,  "color": "#FFD700", "animation": "shine"},
                {"type": "planet", "x": 295, "y": 300, "size": 60,  "color": "#C9A029", "animation": "rotate"},
                {"type": "planet", "x": 430, "y": 300, "size": 48,  "color": "#D4A849", "animation": "rotate"},
                {"type": "planet", "x": 555, "y": 300, "size": 36,  "color": "#87CEEB", "animation": "rotate"},
                {"type": "planet", "x": 645, "y": 300, "size": 34,  "color": "#4169E1", "animation": "rotate"},
                {"type": "label",  "x": 295, "y": 250, "text": "Jupiter", "fontSize": 12, "color": "#A57D20", "animation": "appear"},
                {"type": "label",  "x": 430, "y": 245, "text": "Saturn",  "fontSize": 12, "color": "#A57D20", "animation": "appear"},
                {"type": "label",  "x": 555, "y": 253, "text": "Uranus",  "fontSize": 12, "color": "#006994", "animation": "appear"},
                {"type": "label",  "x": 645, "y": 255, "text": "Neptune", "fontSize": 12, "color": "#1A237E", "animation": "appear"},
            ],
        },
        {
            "id": "summary",
            "startTime": 28000,
            "duration": 12000,
            "text": "Our Solar System formed 4.6 billion years ago from a cloud of gas and dust. Gravity shaped everything. The Sun → Rocky Planets → Gas Giants → Icy Edge.",
            "actors": [
                {"type": "sun",    "x": 80,  "y": 300, "size": 55,  "color": "#FFD700", "animation": "shine", "rays": True},
                {"type": "planet", "x": 185, "y": 300, "size": 14,  "color": "#9E9E9E", "animation": "rotate"},
                {"type": "planet", "x": 240, "y": 300, "size": 20,  "color": "#E8D44D", "animation": "rotate"},
                {"type": "planet", "x": 310, "y": 300, "size": 26,  "color": "#4A90E2", "animation": "rotate"},
                {"type": "planet", "x": 375, "y": 300, "size": 18,  "color": "#D2553A", "animation": "rotate"},
                {"type": "planet", "x": 470, "y": 300, "size": 48,  "color": "#C9A029", "animation": "rotate"},
                {"type": "planet", "x": 580, "y": 300, "size": 36,  "color": "#D4A849", "animation": "rotate"},
                {"type": "planet", "x": 660, "y": 300, "size": 28,  "color": "#87CEEB", "animation": "rotate"},
                {"type": "planet", "x": 730, "y": 300, "size": 26,  "color": "#4169E1", "animation": "rotate"},
                {"type": "label",  "x": 400, "y": 220, "text": "8 Planets orbiting the Sun", "fontSize": 15, "color": "#1A237E", "animation": "appear"},
                {"type": "label",  "x": 400, "y": 540, "text": "Gravity holds the Solar System together", "fontSize": 13, "color": "#4A148C", "animation": "appear"},
            ],
        },
    ],
}

# ─── ROCK CYCLE ───────────────────────────────────────────────────────────────

ROCK_CYCLE_SCRIPT: Dict[str, Any] = {
    "title": "The Rock Cycle: Rocks Are Always Changing",
    "duration": 42000,
    "scenes": [
        {
            "id": "intro",
            "startTime": 0,
            "duration": 6000,
            "text": "Rocks are not permanent — they transform over millions of years. The rock cycle shows how igneous, sedimentary, and metamorphic rocks continuously change into each other.",
            "actors": [
                {"type": "volcano",  "x": 400, "y": 350, "size": 100, "color": "#FF5722", "animation": "pulse"},
                {"type": "mountain", "x": 200, "y": 340, "size": 110, "color": "#795548", "animation": "idle"},
                {"type": "label",    "x": 400, "y": 180, "text": "The Rock Cycle",  "fontSize": 19, "color": "#BF360C", "animation": "appear"},
                {"type": "label",    "x": 400, "y": 545, "text": "Rocks change form over millions of years", "fontSize": 13, "color": "#4E342E", "animation": "appear"},
            ],
        },
        {
            "id": "igneous",
            "startTime": 6000,
            "duration": 8000,
            "text": "Step 1 — Igneous Rock: Magma (molten rock) erupts as lava through volcanoes. As it cools and solidifies, it forms igneous rocks like basalt and granite.",
            "actors": [
                {"type": "volcano",  "x": 400, "y": 370, "size": 100, "color": "#FF5722", "animation": "pulse"},
                {"type": "molecule", "x": 320, "y": 300, "moleculeType": "magma", "size": 28, "color": "#FF3D00", "animation": "bubbleUp"},
                {"type": "molecule", "x": 400, "y": 285, "moleculeType": "magma", "size": 28, "color": "#FF3D00", "animation": "bubbleUp"},
                {"type": "molecule", "x": 480, "y": 295, "moleculeType": "magma", "size": 28, "color": "#FF7043", "animation": "bubbleUp"},
                {"type": "rock",     "x": 560, "y": 390, "size": 40,  "color": "#546E7A", "animation": "appear"},
                {"type": "arrow",    "x": 480, "y": 360, "length": 60, "angle": 0.6, "color": "#546E7A", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 580, "y": 445, "text": "Igneous Rock", "fontSize": 14, "color": "#37474F", "animation": "appear"},
                {"type": "label",    "x": 340, "y": 215, "text": "Lava cools → solidifies", "fontSize": 13, "color": "#BF360C", "animation": "appear"},
            ],
        },
        {
            "id": "weathering",
            "startTime": 14000,
            "duration": 8000,
            "text": "Step 2 — Weathering & Erosion: Wind, rain, and ice slowly break rocks into tiny fragments called sediment. Rivers carry sediment to oceans and lakes.",
            "actors": [
                {"type": "mountain", "x": 250, "y": 330, "size": 110, "color": "#795548", "animation": "idle"},
                {"type": "cloud",    "x": 320, "y": 150, "size": 58,  "color": "#90A4AE", "animation": "sway"},
                {"type": "molecule", "x": 300, "y": 210, "moleculeType": "water", "size": 22, "color": "#42A5F5", "animation": "fall"},
                {"type": "molecule", "x": 350, "y": 390, "moleculeType": "sediment", "size": 20, "color": "#A1887F", "animation": "moveDown"},
                {"type": "molecule", "x": 400, "y": 400, "moleculeType": "sediment", "size": 20, "color": "#A1887F", "animation": "moveDown"},
                {"type": "arrow",    "x": 370, "y": 390, "length": 160, "angle": 0.5, "color": "#5D4037", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 530, "y": 440, "text": "Sediment → deposited", "fontSize": 14, "color": "#4E342E", "animation": "appear"},
                {"type": "label",    "x": 250, "y": 200, "text": "Rain erodes rock", "fontSize": 13, "color": "#0288D1", "animation": "appear"},
            ],
        },
        {
            "id": "sedimentary",
            "startTime": 22000,
            "duration": 8000,
            "text": "Step 3 — Sedimentary Rock: Layers of sediment pile up and compress over millions of years. The pressure cements particles together forming sedimentary rock.",
            "actors": [
                {"type": "ocean",    "x": 500, "y": 430, "size": 180, "color": "#1565C0", "animation": "wave"},
                {"type": "molecule", "x": 430, "y": 390, "moleculeType": "sediment", "size": 22, "color": "#A1887F", "animation": "moveDown"},
                {"type": "molecule", "x": 480, "y": 400, "moleculeType": "sediment", "size": 22, "color": "#8D6E63", "animation": "moveDown"},
                {"type": "rock",     "x": 480, "y": 465, "size": 50,  "color": "#8D6E63", "animation": "appear"},
                {"type": "arrow",    "x": 480, "y": 440, "length": 60, "angle": 1.5708, "color": "#4E342E", "thickness": 4, "animation": "pulse"},
                {"type": "label",    "x": 480, "y": 520, "text": "Sedimentary Rock", "fontSize": 14, "color": "#3E2723", "animation": "appear"},
                {"type": "label",    "x": 300, "y": 390, "text": "Layers compress under pressure", "fontSize": 13, "color": "#4E342E", "animation": "appear"},
            ],
        },
        {
            "id": "metamorphic",
            "startTime": 30000,
            "duration": 6000,
            "text": "Step 4 — Metamorphic Rock: Deep underground, extreme heat and pressure transform existing rocks. They don't melt — they recrystallize into metamorphic rocks like marble.",
            "actors": [
                {"type": "rock",     "x": 350, "y": 350, "size": 50,  "color": "#8D6E63", "animation": "vibrate"},
                {"type": "bolt",     "x": 350, "y": 350, "size": 40,  "color": "#FF7043", "animation": "pulse"},
                {"type": "arrow",    "x": 350, "y": 280, "length": 60, "angle": 1.5708, "color": "#FF5722", "thickness": 4, "animation": "pulse"},
                {"type": "arrow",    "x": 350, "y": 420, "length": 60, "angle": -1.5708, "color": "#FF5722", "thickness": 4, "animation": "pulse"},
                {"type": "rock",     "x": 530, "y": 350, "size": 55,  "color": "#CE93D8", "animation": "appear"},
                {"type": "label",    "x": 350, "y": 220, "text": "Heat + Pressure", "fontSize": 14, "color": "#BF360C", "animation": "appear"},
                {"type": "label",    "x": 530, "y": 425, "text": "Metamorphic Rock", "fontSize": 14, "color": "#7B1FA2", "animation": "appear"},
            ],
        },
        {
            "id": "summary",
            "startTime": 36000,
            "duration": 6000,
            "text": "The Rock Cycle never ends: Magma → Igneous → Weathering → Sedimentary → Heat/Pressure → Metamorphic → Melts again → Magma. Rocks are always transforming!",
            "actors": [
                {"type": "volcano",  "x": 400, "y": 370, "size": 70,  "color": "#FF5722", "animation": "pulse"},
                {"type": "rock",     "x": 220, "y": 330, "size": 40,  "color": "#546E7A", "animation": "idle"},
                {"type": "rock",     "x": 580, "y": 340, "size": 40,  "color": "#8D6E63", "animation": "idle"},
                {"type": "rock",     "x": 400, "y": 240, "size": 40,  "color": "#CE93D8", "animation": "idle"},
                {"type": "arrow",    "x": 240, "y": 310, "length": 130, "angle": -0.8, "color": "#FF9800", "thickness": 3, "animation": "appear"},
                {"type": "arrow",    "x": 440, "y": 285, "length": 120, "angle": 0.9, "color": "#FF9800", "thickness": 3, "animation": "appear"},
                {"type": "label",    "x": 400, "y": 170, "text": "Igneous → Sedimentary → Metamorphic → Magma", "fontSize": 12, "color": "#BF360C", "animation": "appear"},
                {"type": "label",    "x": 400, "y": 545, "text": "The Endless Rock Cycle", "fontSize": 16, "color": "#4E342E", "animation": "appear"},
            ],
        },
    ],
}

# ─── Registry & Lookup ────────────────────────────────────────────────────────

PREBUILT_SCRIPTS: Dict[str, Dict[str, Any]] = {
    # Water Cycle
    "water cycle": WATER_CYCLE_SCRIPT,
    "the water cycle": WATER_CYCLE_SCRIPT,
    "watercycle": WATER_CYCLE_SCRIPT,
    "hydrological cycle": WATER_CYCLE_SCRIPT,
    "evaporation": WATER_CYCLE_SCRIPT,
    "precipitation": WATER_CYCLE_SCRIPT,
    "condensation": WATER_CYCLE_SCRIPT,
    # Photosynthesis
    "photosynthesis": PHOTOSYNTHESIS_SCRIPT,
    "how plants make food": PHOTOSYNTHESIS_SCRIPT,
    "how do plants make food": PHOTOSYNTHESIS_SCRIPT,
    "plant food making": PHOTOSYNTHESIS_SCRIPT,
    "chlorophyll": PHOTOSYNTHESIS_SCRIPT,
    "light reactions": PHOTOSYNTHESIS_SCRIPT,
    "calvin cycle": PHOTOSYNTHESIS_SCRIPT,
    # Gravity
    "gravity": GRAVITY_SCRIPT,
    "gravitational force": GRAVITY_SCRIPT,
    "how gravity works": GRAVITY_SCRIPT,
    "newtons gravity": GRAVITY_SCRIPT,
    "newton's gravity": GRAVITY_SCRIPT,
    "law of gravity": GRAVITY_SCRIPT,
    "universal gravitation": GRAVITY_SCRIPT,
    # Solar System
    "solar system": SOLAR_SYSTEM_SCRIPT,
    "the solar system": SOLAR_SYSTEM_SCRIPT,
    "our solar system": SOLAR_SYSTEM_SCRIPT,
    "planets": SOLAR_SYSTEM_SCRIPT,
    "the planets": SOLAR_SYSTEM_SCRIPT,
    # Rock Cycle
    "rock cycle": ROCK_CYCLE_SCRIPT,
    "the rock cycle": ROCK_CYCLE_SCRIPT,
    "types of rocks": ROCK_CYCLE_SCRIPT,
    "igneous sedimentary metamorphic": ROCK_CYCLE_SCRIPT,
}

# Exemplars used in prompts — indexed by domain for best-match injection
EXEMPLARS: Dict[str, Dict[str, Any]] = {
    "biology":      PHOTOSYNTHESIS_SCRIPT,
    "earth_science": WATER_CYCLE_SCRIPT,
    "physics":      GRAVITY_SCRIPT,
    "astronomy":    SOLAR_SYSTEM_SCRIPT,
    "chemistry":    PHOTOSYNTHESIS_SCRIPT,
    "generic":      WATER_CYCLE_SCRIPT,
}


def _clean_concept(concept: str) -> str:
    """Extract short topic even if user pastes a long paragraph."""
    text = (concept or "").lower().strip()
    if len(text) > 120:
        for kw, canonical in [
            ("photosynthesis", "photosynthesis"),
            ("water cycle", "water cycle"),
            ("evaporation", "water cycle"),
            ("precipitation", "water cycle"),
            ("gravity", "gravity"),
            ("solar system", "solar system"),
            ("rock cycle", "rock cycle"),
            ("igneous", "rock cycle"),
        ]:
            if kw in text:
                return canonical
    return concept.strip()


def get_prebuilt_script(concept: str) -> Optional[Dict[str, Any]]:
    """Return a prebuilt script for the concept if one exists, else None."""
    key = _clean_concept(concept).lower()
    return PREBUILT_SCRIPTS.get(key)


def get_exemplar_for_domain(domain: str) -> Dict[str, Any]:
    """Return the best exemplar script for a given domain (for prompt injection)."""
    return EXEMPLARS.get(domain.lower(), WATER_CYCLE_SCRIPT)
