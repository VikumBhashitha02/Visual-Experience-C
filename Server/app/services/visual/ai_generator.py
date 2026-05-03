"""
AI generator – Google Gemini for concept analysis and animation script generation.
Uses GEMINI_API_KEY or Gemini_API_Key from .env; model gemini-2.0-flash (free tier).
"""
import json
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.config import settings
from app.services.visual.layout_engine import get_actor_properties

logger = logging.getLogger(__name__)

load_dotenv()

_client: Optional[genai.Client] = None


def _get_api_key() -> str:
    """Read Gemini API key from config or env (supports GEMINI_API_KEY and Gemini_API_Key)."""
    key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("Gemini_API_Key")
        or ""
    )
    return key.strip()


def _get_model_name() -> str:
    return getattr(settings, "GEMINI_MODEL", None) or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def get_client() -> genai.Client:
    """Get or create Gemini Client for the Gemini API."""
    global _client
    if _client is not None:
        return _client
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY (or Gemini_API_Key) is not set. Please set it in your .env file.")
    _client = genai.Client(api_key=api_key)
    return _client


def _generate_text(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    """Call Gemini and return response text."""
    client = get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    response = client.models.generate_content(
        model=_get_model_name(),
        contents=prompt,
        config=config,
    )
    if not response or not response.text:
        raise RuntimeError("Gemini returned empty response")
    return response.text.strip()


VALID_ACTOR_TYPES = {
    # Astronomy
    "planet", "earth", "moon", "star", "sun", "asteroid", "comet",
    # Earth Science
    "cloud", "mountain", "ocean", "volcano", "rock",
    # Biology
    "animal", "cell", "bacteria", "leaf", "root", "plant",
    # Chemistry / Physics
    "molecule", "atom", "electron", "proton", "neutron", "glucose",
    # Visual Aids
    "arrow", "label", "line", "graph", "number", "bolt", "thermometer", "wave",
}

VALID_ANIMATIONS = {
    "appear", "idle", "moveUp", "moveDown", "floatIn", "floatOut",
    "glow", "shine", "bubbleUp", "rotate", "pulse", "wave",
    "sway", "grow", "absorb", "orbit", "spin", "vibrate", "fall",
}

KEYWORD_VISUAL_MAP = [
    (["gravity", "gravitational"], "earth", "idle"),
    (["fall", "falling", "drop", "downward", "down"], "arrow", "moveDown"),
    (["pull", "attract", "attraction", "pulls", "pulling"], "arrow", "moveDown"),
    (["orbit", "orbiting", "around"], "moon", "rotate"),
    (["force"], "number", "pulse"),
    (["mass", "heavier", "lighter"], "number", "pulse"),
    (["earth"], "earth", "idle"),
    (["planet"], "planet", "idle"),
    (["moon"], "moon", "idle"),
    (["star", "sun"], "star", "shine"),
    (["space", "universe", "galaxy"], "star", "shine"),
    (["cell", "cells"], "cell", "pulse"),
    (["bacteria", "bacterium"], "bacteria", "pulse"),
    (["leaf", "leaves"], "leaf", "idle"),
    (["root", "roots"], "root", "idle"),
    (["plant", "plants"], "plant", "grow"),
    (["sunlight", "light"], "sun", "shine"),
    (["photosynthesis", "chloroplast", "chlorophyll"], "cell", "pulse"),
    (["glucose", "sugar"], "glucose", "appear"),
    (["oxygen", "o2"], "label", "appear"),
    (["carbon dioxide", "co2", "dioxide"], "label", "appear"),
    (["animal", "animals"], "animal", "idle"),
    (["atom", "atoms"], "atom", "pulse"),
    (["molecule", "molecules"], "molecule", "pulse"),
    (["electron", "electrons"], "electron", "rotate"),
    (["proton", "protons"], "proton", "rotate"),
    (["neutron", "neutrons"], "neutron", "rotate"),
    (["increase", "decrease", "rise", "falling", "grows", "shrinks"], "graph", "appear"),
    (["direction", "toward", "away"], "arrow", "moveDown"),
    (["number", "amount", "how many"], "number", "pulse"),
    (["label", "name", "term", "definition"], "label", "appear"),
    (["line", "connect", "link"], "line", "appear"),
    (["explain", "explanation", "because"], "label", "appear"),
]


# ─── Cognitive Load Configuration ───────────────────────────────────────────
#
# KEY DESIGN PRINCIPLE (MANDATORY - do NOT simplify these back):
#
#  LOW    → MORE scenes, FEWER actors, SLOW animations, ISOLATED focus
#           Beginner learners cannot handle parallel information.
#           Each scene = ONE object doing ONE thing. Repetition is good.
#
#  MEDIUM → BALANCED scenes, MODERATE actors, CAUSE→EFFECT chains
#           Intermediate learners can track 2-3 interacting elements.
#           Each scene = one interaction with a visible outcome.
#
#  HIGH   → FEWER scenes, MOST actors, PARALLEL processes, SYSTEM-WIDE view
#           Advanced learners benefit from seeing the full system at once.
#           Each scene = multiple simultaneous processes forming a whole.
#
# ⚠️ These are NOT just speed/color changes — they are COMPLETELY DIFFERENT
#    visual pedagogical strategies.
# ─────────────────────────────────────────────────────────────────────────────

_LOAD_CONFIG = {
    "low": {
        # MORE scenes — each teaching ONE thing at a time (progressive disclosure)
        "scene_count": "7–9",
        "actors_per_scene": "1–2",
        "total_ms": "35000–45000",
        "scene_ms": "4000–5500 each",
        "animations": "appear, idle, grow, pulse, sway",
        "speed": "SLOW — each actor appears alone and holds position for 2+ seconds before anything changes",
        "focus": "ISOLATED — one object, one action, one idea per scene. No interactions.",
        "text_style": "One sentence maximum. Everyday words only. No formulas. Like explaining to a 7-year-old.",
        "complexity": (
            "STRICTLY one main actor per scene. Show it, name it, animate it — nothing else. "
            "Use REPETITION: if water appears in scene 2, show it again in scene 4 in a new state. "
            "NO arrows. NO simultaneous processes. NO labels except the object name."
        ),
        "scene_archetypes": (
            "HOOK (1 actor, just appears) → "
            "INTRODUCE_OBJECT_1 (show it alone, name it) → "
            "SHOW_OBJECT_1_STATE (animate it doing its one thing) → "
            "INTRODUCE_OBJECT_2 (new actor, shown alone) → "
            "SHOW_OBJECT_2_STATE → "
            "SHOW_CONNECTION (only now show both together, ONE simple relationship) → "
            "GENTLE_SUMMARY (same 2 actors, simple label)"
        ),
        "visual_rules": (
            "HUGE actors (size 80–120). ONE actor fills most of the scene. "
            "Very bright, saturated, friendly colors. No visual clutter. "
            "Empty space is GOOD — it reduces cognitive load. "
            "Center each actor. Max 1 label (the object name only)."
        ),
        "actor_strategy": (
            "Choose only the SINGLE most important actor for the concept. "
            "For photosynthesis: show ONLY the sun in scene 1, ONLY the plant in scene 2. "
            "Do NOT combine them until scene 5+."
        ),
        "do_not": (
            "NEVER show more than 2 actors simultaneously. "
            "NEVER use arrows (they imply relationships — too complex for LOW). "
            "NEVER show chemical formulas. NEVER animate two things at once. "
            "NEVER use floatIn, floatOut, absorb, orbit, vibrate, or rotate."
        ),
    },
    "medium": {
        # BALANCED scenes — show interactions, not just isolated objects
        "scene_count": "5–7",
        "actors_per_scene": "2–4",
        "total_ms": "30000–42000",
        "scene_ms": "5000–7000 each",
        "animations": "appear, glow, shine, bubbleUp, moveUp, moveDown, floatIn, floatOut, absorb, fall, pulse, sway, rotate",
        "speed": "MEDIUM — actors appear one at a time but interact within the same scene",
        "focus": "INTERACTION — clearly show A causes B. Every scene has a cause and a visible effect.",
        "text_style": "2 sentences. First: name the scientific term. Second: explain the cause→effect in plain language.",
        "complexity": (
            "Each scene shows ONE cause-effect pair. Actor A does something → Actor B responds visibly. "
            "Use arrows to connect the cause to the effect. "
            "Add a label with the scientific name near the key actor. "
            "Introduce chemical formulas ONLY in the final summary scene."
        ),
        "scene_archetypes": (
            "HOOK (2 actors establish the setting) → "
            "INTRODUCE_CAUSE (show the cause actor, label it) → "
            "SHOW_CAUSE_ACTION (cause actor animates — glow, pulse, shine) → "
            "SHOW_EFFECT (effect actor responds — appears, grows, moves) → "
            "ADD_ARROW (arrow connects cause to effect, reveals the relationship) → "
            "SUMMARY_WITH_FORMULA (both actors + equation label)"
        ),
        "visual_rules": (
            "Use arrows to visually link every cause to its effect. "
            "Color-code: same substance always the same color across scenes. "
            "Labels for scientific terms (fontSize 15–16). "
            "Actors 50–90 in size. 2–4 actors per scene — not cluttered, not empty."
        ),
        "actor_strategy": (
            "Select actors that have a clear relationship. Always show the CAUSE actor first, "
            "then add the EFFECT actor in the same scene. "
            "Use one arrow to connect them visually. "
            "For photosynthesis: sun + leaf together, arrow from sun to leaf."
        ),
        "do_not": (
            "NEVER show parallel simultaneous processes in the same scene. "
            "NEVER skip the cause — always show WHAT caused WHAT. "
            "NEVER use more than 4 actors in one scene. "
            "NEVER show the full system in one scene (save that for HIGH)."
        ),
    },
    "high": {
        # FEWER scenes — show the whole system working together
        "scene_count": "3–5",
        "actors_per_scene": "4–8",
        "total_ms": "25000–35000",
        "scene_ms": "6000–9000 each",
        "animations": "all: appear, glow, shine, bubbleUp, moveUp, moveDown, floatIn, floatOut, absorb, fall, vibrate, pulse, orbit, spin, wave, rotate, sway",
        "speed": "FAST transitions — actors appear in rapid succession within each scene",
        "focus": "SYSTEM-WIDE — show the ENTIRE process as one unified system, all parts active simultaneously",
        "text_style": (
            "2–3 sentences. Use precise scientific terminology. "
            "State the mechanism, the simultaneous sub-processes, and the net outcome. "
            "Include the governing equation or law."
        ),
        "complexity": (
            "Each scene shows MULTIPLE simultaneous processes. "
            "All relevant actors are ACTIVE at the same time. "
            "Multiple arrows showing parallel flows. "
            "Include feedback loops (A→B→A or cyclic arrows). "
            "Show the system's EMERGENT BEHAVIOR — what only becomes visible when all parts run together."
        ),
        "scene_archetypes": (
            "FULL_SYSTEM_OVERVIEW (all major actors appear at once, each in its natural position) → "
            "PARALLEL_INPUTS (show all inputs entering the system simultaneously) → "
            "MECHANISM_IN_ACTION (all transformations happening at once, multiple arrows) → "
            "FEEDBACK_AND_OUTPUTS (outputs feeding back + leaving system) → "
            "EQUATION_SUMMARY (all actors visible + governing equation label, system in steady state)"
        ),
        "visual_rules": (
            "DENSE scenes — 5+ actors all active simultaneously. "
            "Multiple arrows forming a directed network (not just one A→B). "
            "Smaller actors (30–60) to fit more on screen without overlap. "
            "Scientific formulas as label actors. Color-coded subsystems. "
            "Show feedback loops: cyclic arrow paths."
        ),
        "actor_strategy": (
            "Place ALL major actors of the concept in scene 1 simultaneously. "
            "Use position to encode role: inputs on left, process in center, outputs on right. "
            "Multiple arrows form a network. Labels contain chemical formulas. "
            "For photosynthesis: sun + CO2 molecules + leaf + chloroplast + glucose + O2 + arrows ALL in scene 2."
        ),
        "do_not": (
            "NEVER show only one actor per scene. "
            "NEVER isolate steps — the whole point is simultaneous system behavior. "
            "NEVER use fewer than 4 actors per scene. "
            "NEVER omit feedback loops for cyclic processes. "
            "NEVER write a summary without the governing equation."
        ),
    },
}


def _get_load_config(cognitive_load: str) -> dict:
    """Return load configuration dict for the given cognitive load level."""
    return _LOAD_CONFIG.get((cognitive_load or "medium").lower(), _LOAD_CONFIG["medium"])


# ─── Domain Actor Vocabulary + Visual Metaphors ───────────────────────────────

_DOMAIN_ACTORS = {
    "biology": (
        "plant (green plant body, x≈350 y≈340), leaf (chloroplast site, glow when active), "
        "root (water absorption, absorb animation), sun (light energy source, top-right, shine+rays), "
        "molecule with moleculeType=water (blue, bubbleUp from roots), "
        "molecule with moleculeType=co2 (grey, floatIn from air), "
        "molecule with moleculeType=o2 (green, floatOut upward), "
        "glucose (orange, appear in leaf after reaction), "
        "cell (biology unit, pulse when active), animal (consumer, idle), bolt (energy flash)"
    ),
    "earth_science": (
        "ocean (deep blue, bottom y≈460), cloud (white/grey, top y≈130, floatIn), "
        "mountain (brown, right side), volcano (red, pulse/erupt), "
        "molecule with moleculeType=water (blue, bubbleUp from ocean OR moveDown as rain), "
        "molecule with moleculeType=sediment (brown, moveDown), "
        "molecule with moleculeType=magma (orange-red, bubbleUp from volcano), "
        "molecule with moleculeType=rock (grey, appear/idle), "
        "plant (green vegetation, center), arrow (flow direction, thick)"
    ),
    "physics": (
        "ELECTROMAGNETICS/MAGNETISM concepts: "
        "line (wire, VERTICAL center x=400, y=100-y=500, size=8-15, color=#FF9800, idle — NOT huge), "
        "electron (small blue dot, size=20-30, moveUp along wire to show conventional current direction), "
        "wave (magnetic field ring, size=40-100, color=#9C27B0 purple for magnetic, rotate clockwise for outward field), "
        "arrow (field vector or force direction, angle must show circular field: use multiple arrows at different y positions), "
        "bolt (electromagnetic energy, gold #FFD700, pulse), "
        "label (formula: 'B = mu_0*I/2pi*r' or 'Right-Hand Rule', fontSize=16), "
        "thermometer (field strength indicator, scale with current)."
        "GRAVITY/MECHANICS concepts: "
        "earth (large blue sphere, center-bottom y>400), moon (grey, orbit), rock (falling object, fall), "
        "arrow (force vector, thick, colored by direction), label (formula/value, near subject, fontSize 16), "
        "bolt (energy/force flash), star (distant, small, shine)"
    ),
    "astronomy": (
        "sun (large gold star, center or left, shine+rays), "
        "planet (coloured sphere, orbit around sun), moon (grey, orbit around planet), "
        "star (distant white/yellow, small, shine), "
        "asteroid (small brown rock, spin+fall), comet (white streak, moveDown), "
        "bolt (nuclear fusion energy inside sun), arrow (orbital path / gravitational force)"
    ),
    "chemistry": (
        "atom (element sphere — color by element: H=white, O=red, C=grey, N=blue), "
        "electron (small yellow, orbit animation around atom), "
        "proton (red, inside atom nucleus), neutron (grey, inside nucleus), "
        "molecule (compound formed from atoms — moleculeType: water/co2/o2), "
        "glucose (orange hexagon shape), "
        "arrow (reaction direction, bold, between reactants and products), "
        "label (chemical formula, e.g. 'H₂O', 'CO₂', fontSize 16)"
    ),
    "generic": (
        "arrow (show direction of any flow/force), label (name any concept or term), "
        "molecule (represent any substance with moleculeType), "
        "plant (biological subject), planet (astronomical/large scale subject), "
        "bolt (represent energy, power, or force), sun (represent a source or energy)"
    ),
}


# ─── Positioning Blueprint ────────────────────────────────────────────────────

_POSITION_BLUEPRINT = """
NATURAL POSITIONING RULES (always follow):
  Sun / Star:       x=680-720, y=60-100   (top-right, large size=80-120, gold #FFD700)
  Sky / Clouds:     x=120-650, y=100-180  (top area, white/grey)
  Mountain:         x=550-720, y=200-380  (right side)
  Plant / Tree:     x=280-420, y=250-400  (center-left, green)
  Ocean / Water:    x=200-600, y=420-480  (bottom, deep blue #1565C0)
  Volcano:          x=600-700, y=300-420  (right side, dark red)
  Root / Soil:      x=280-420, y=430-520  (below plant)
  Wire (line):      x=400, y=150-500 VERTICAL (THIN size=8-15, NOT size=80+ )
  Electrons:        x=380-420, y=400 moving to y=100 (moveUp along wire)
  Field rings:      x=300-500 around wire, size=40 to 120 (wave, rotate)
  Field arrows:     placed at wire radius, pointing tangentially around wire
  Molecules:        spread around x=150-600, y=150-480 (near their source actor)
  Arrows:           positioned between cause-actor and effect-actor
  Labels:           20-30px above or to the right of their subject actor
  Equations:        x=200-600, y=250-350  (center of scene, large fontSize=16-18)

SCREEN BOUNDS: x must be 60-740, y must be 60-540. Nothing outside these bounds.
ACTOR SIZE BOUNDS: size must be 10-120. NEVER use size > 120. A 'line' wire should be size=10-15 (thickness), not size=480.
ELECTROMAGNETISM CONVENTIONS:
  - Wire = vertical line, thin (size=10)
  - Magnetic field = concentric rings (wave, rotate) around wire
  - Current direction = electron moveUp (conventional current, positive direction)
  - Field direction = Right-Hand Rule: curl fingers around wire in direction of B
  - Field outside wire weakens with distance: inner ring larger, outer ring smaller
  - Multiple wave rings at different distances show field gradient
"""


# ─── Scene Archetype Blueprints ───────────────────────────────────────────────

_ARCHETYPE_BLUEPRINTS = """
SCENE ARCHETYPES — use these to design each scene:

  HOOK:              1-2 large actors appear. No action yet. Establish sense of scale.
                     Example: Huge sun appears top-right. Earth appears center-bottom.

  INTRODUCE_AGENT:   The main "doing" actor appears. It should be the biggest, most colorful.
                     Show it with a label naming it scientifically.

  SHOW_CAUSE:        Introduce the cause. Use arrow pointing FROM the cause TO the effect.
                     Animate the cause actor (pulse, glow, shine).

  SHOW_EFFECT:       The effect actor responds (grows, moves, appears, changes color).
                     Arrow now points at the effect. Label the change.

  SHOW_TRANSFORMATION: An actor changes state (liquid→gas: bubbleUp; solid→liquid: vibrate+glow).
                     The old state actor fades while the new one appears.

  SHOW_FEEDBACK_LOOP: TWO arrows forming a cycle. Actor A → Actor B → Actor A.
                     Show interdependence visually.

  SUMMARY:           Show ALL key actors together at once. Add equation/formula label in center.
                     Each actor should be in its final correct animation state.
"""


# ─── Scene Template ───────────────────────────────────────────────────────────

# ─── Scene Template (Clean Visual Schema) ────────────────────────────────────
# This is the NEW format. The validator normalises it to backend-compatible JSON.

_SCENE_TEMPLATE = """{
  "id": "<descriptive_id: wire_appears | field_forms | right_hand_rule | summary>",
  "startTime": <cumulative ms — must equal sum of all previous scene durations>,
  "duration": <milliseconds per cognitive load rules>,
  "focus": "<MAX 6 WORDS. What this scene teaches: 'Sun emits light energy' NOT a paragraph>",
  "text": "<MAX 1 sentence. Simple caption for the student. NO paragraphs. NO formulas except in summary.>",
  "actors": [
    {
      "id": "<unique id: sun_1 | leaf_1 | co2_a>",
      "type": "<VALID actor type>",
      "role": "<1–3 words: energy source | absorbs CO2 | field boundary>",
      "x": <60–740>,
      "y": <60–540>,
      "size": <18–100, larger = more important>,
      "color": "<#RRGGBB>",
      "animation": "<VALID animation>",

      // Type-specific fields (ONLY include for these types):
      "moleculeType": "<water|co2|o2|magma|sediment|rock>"   // molecule only
      "text": "<label string — max 4 words>"                  // label only
      "fontSize": <14–18>                                     // label only
      "angle": <radians>, "length": <px>, "thickness": <2–5>  // arrow only
      "rays": true                                             // sun only
    }
  ],
  "animations": [
    {
      "type": "<emit | flow | absorb | transform | orbit | repel | attract>",
      "from": "<actor id>",
      "to": "<actor id>",
      "duration": <ms — must be <= scene duration>
    }
  ]
}"""


# ─── Main Prompt Builder ──────────────────────────────────────────────────────

def build_prompt_for_load(
    concept: str,
    cognitive_load: str = "medium",
    domain: str = "generic",
) -> str:
    """
    Build a world-class, cognitively-adaptive educational animation prompt.

    Args:
        concept:        The educational concept to animate.
        cognitive_load: 'low' | 'medium' | 'high'
        domain:         Domain from concept analysis (biology, physics, etc.)

    Returns:
        Fully-formed prompt string for Gemini.
    """
    cfg = _get_load_config(cognitive_load)
    domain_actors = _DOMAIN_ACTORS.get(domain.lower(), _DOMAIN_ACTORS["generic"])

    from app.services.visual.prebuilt import get_exemplar_for_domain
    exemplar = get_exemplar_for_domain(domain)
    trimmed_exemplar = {
        "title": exemplar["title"],
        "duration": exemplar["duration"],
        "scenes": exemplar["scenes"][:4],
    }

    load_label = cognitive_load.upper()

    return f"""\
You are simultaneously:
  ✦ A world-class educational animator (like a PBS/BBC documentary director)
  ✦ A cognitive science expert (applying Mayer's Dual Coding + Sweller's CLT)
  ✦ A simulation engine designer (every actor must earn its place on screen)
  ✦ A visual storytelling expert (cause → effect is your narrative engine)

Your task: Turn "{concept}" into a VISUAL LEARNING EXPERIENCE.
Not a slideshow. Not a list of facts. A SIMULATION that teaches by SHOWING.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCEPT:         {concept}
COGNITIVE LOAD:  {load_label}
DOMAIN:          {domain.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

════════════════════════════════════════
  MANDATORY THINKING PROCESS (internal)
════════════════════════════════════════
Before generating any scene, you MUST mentally:
  1. Break "{concept}" into 4–7 learning STEPS (not just facts)
  2. For each step, ask:
       → What is the CAUSE?
       → What is the EFFECT?
       → What MOVES? What TRANSFORMS? What REACTS?
       → Can I make the invisible VISIBLE? (forces, fields, processes)
  3. Choose a visual METAPHOR for each abstract idea
  4. Design each scene like a STORYBOARD PANEL: one clear action, one clear meaning

════════════════════════════════════════
  THIS IS COGNITIVE LOAD LEVEL: {load_label}
════════════════════════════════════════

⚠️  CRITICAL: The three cognitive load levels produce COMPLETELY DIFFERENT visual strategies.
    This is NOT a speed or color change — it is a fundamentally different pedagogical approach.

MANDATORY STRUCTURAL DIFFERENCES (you MUST enforce these):
┌──────────────────┬──────────────┬────────────────┬──────────────────┐
│ Element          │ LOW          │ MEDIUM         │ HIGH             │
├──────────────────┼──────────────┼────────────────┼──────────────────┤
│ Scene Count      │ MORE (7–9)  │ Balanced (5–7) │ FEWER (3–5)      │
│ Actors/scene     │ 1–2 ONLY    │ 2–4            │ 4–8 REQUIRED     │
│ Animation style  │ ONE per scene│ Cause→Effect   │ PARALLEL (many)  │
│ Speed            │ SLOW         │ MEDIUM         │ FAST transitions │
│ Visual focus     │ ISOLATED obj │ INTERACTION    │ FULL SYSTEM      │
│ Arrows           │ FORBIDDEN    │ 1 per scene    │ NETWORK of arrows│
│ Formulas         │ FORBIDDEN    │ Summary only   │ Every scene      │
└──────────────────┴──────────────┴────────────────┴──────────────────┘

YOUR CURRENT LEVEL ({load_label}) RULES:
  Scene count:        {cfg['scene_count']}
  Actors per scene:   {cfg['actors_per_scene']}
  Total duration:     {cfg['total_ms']} ms
  Per-scene duration: {cfg['scene_ms']}
  Animation speed:    {cfg.get('speed', cfg['animations'])}
  Visual focus:       {cfg.get('focus', cfg['complexity'])}
  Animations allowed: {cfg['animations']}
  Narration style:    {cfg['text_style']}
  Visual complexity:  {cfg['complexity']}
  Actor strategy:     {cfg.get('actor_strategy', 'Use domain-appropriate actors.')}
  Scene archetypes:   {cfg['scene_archetypes']}
  Visual rules:       {cfg['visual_rules']}
  STRICTLY AVOID:     {cfg['do_not']}

════════════════════════════════════════
  SCENE ARCHETYPE BLUEPRINTS
════════════════════════════════════════
{_ARCHETYPE_BLUEPRINTS}

════════════════════════════════════════
  POSITIONING BLUEPRINT
════════════════════════════════════════
{_POSITION_BLUEPRINT}

════════════════════════════════════════
  VISUAL ACTOR VOCABULARY — {domain.upper()}
════════════════════════════════════════
Domain-specific actors:
  {domain_actors}

Complete valid actor types:
  sun, cloud, mountain, ocean, volcano, rock,
  plant, leaf, root, animal, cell, bacteria,
  molecule (+ moleculeType: water|co2|o2|glucose|magma|sediment|rock),
  atom, electron, proton, neutron, glucose,
  planet, moon, star, asteroid, comet,
  arrow, label, line, bolt, wave, thermometer

════════════════════════════════════════
  ANIMATION MEANING GUIDE
════════════════════════════════════════
  appear    → something new enters the scene (always start hidden actors with appear)
  idle      → a stable, resting state (no active process)
  glow      → an active process is happening HERE (photosynthesis, reaction)
  pulse     → a force or energy wave is being emitted
  shine     → emitting light or heat (sun, hot object)
  grow      → gaining mass, size, or concentration
  bubbleUp  → rising gas/liquid (evaporation, oxygen released)
  moveUp    → object moving upward (water vapour, warm air)
  moveDown  → flowing downward (rain, runoff, sediment)
  floatIn   → substance ENTERING a system (CO2 entering leaf stomata)
  floatOut  → substance LEAVING a system (O2 released from leaf)
  absorb    → a system taking in a substance (root absorbing water)
  fall      → driven by gravity (object falling, rain drop)
  rotate    → orbital or spinning motion around an axis
  orbit     → circular path around another body
  spin      → self-rotation on own axis
  vibrate   → high-energy excited state (hot molecule, earthquake)
  wave      → oscillating / wave-like propagation
  sway      → gentle lateral movement (plant in breeze)

════════════════════════════════════════
  ACTOR FIELD RULES (STRICT)
════════════════════════════════════════
  id:          REQUIRED. Unique string per actor per scene (sun_1, leaf_1, co2_a)
  type:        MUST be from the valid list above
  role:        1–3 words describing the actor's function (energy source, field ring, output)
  x:           60–740 (horizontal pixel position)
  y:           60–540 (vertical pixel position)
  size:        18–100 (larger = more visually important. NEVER > 100)
  color:       hex #RRGGBB — semantically correct:
                 sun=#FFD700, water=#2196F3, plant=#2E7D32, CO2=#9E9E9E,
                 O2=#81C784, glucose=#FF9800, magma=#FF5722, magnetic=#9C27B0
  animation:   MUST be from valid list. Choose based on meaning guide.

  label type:  MUST have "text" (MAX 4 WORDS) and "fontSize" (14–18)
  arrow type:  MUST have "angle" (radians) + "length" (px) + "thickness" (2–5)
               Angles: 0=right, -1.5708=up, 1.5708=down, 3.14159=left
  molecule:    MUST have "moleculeType" (water|co2|o2|glucose|magma|sediment|rock)
  sun:         MUST have "rays": true

════════════════════════════════════════
  CLEAN UI RULES (MANDATORY)
════════════════════════════════════════
  ⚠️ YOU ARE AN ANIMATOR, NOT A TEXT WRITER.

  TEXT RULES (scene.text and scene.focus):
    scene.focus = MAX 6 WORDS. What happens: "Sun emits light" not "The sun, being the primary..."
    scene.text  = MAX 1 SHORT SENTENCE. A caption. "Electrons flow upward through the wire."
                  NO: paragraphs, explanations, multiple sentences, complex vocabulary

  ACTOR COUNT PER SCENE:
    {cfg['actors_per_scene']} actors MAXIMUM. Blank space = clarity. Clutter = confusion.
    Choose only actors that are DOING something in this scene.

  ANIMATIONS[] ARRAY:
    REQUIRED. Maps actor-to-actor relationships visually.
    Only include animations that SHOW PROCESS (emit, flow, absorb, transform, orbit, attract, repel).
    Do NOT add decorative animations.
    "from" and "to" MUST match actor "id" values in the same scene.

  GOOD SCENE checklist:
    [x] Student understands it WITHOUT reading the text
    [x] ONE teaching moment per scene
    [x] Every actor has a role and is actively animating
    [x] All animations[] reference valid actor ids in this scene
    [x] Label texts are MAX 4 words

  BAD SCENE — reject if:
    [x] scene.text has multiple sentences or technical paragraphs
    [x] Actors just idle with no animations[]
    [x] animations[] references actors not in this scene
    [x] More than {cfg['actors_per_scene'].split('–')[1].strip() if '–' in cfg['actors_per_scene'] else '4'} actors in one scene
    [x] Label text exceeds 4 words

════════════════════════════════════════
  QUALITY EXEMPLAR (match this standard)
════════════════════════════════════════
```json
{json.dumps(trimmed_exemplar, indent=2)}
```

════════════════════════════════════════
  SCENE JSON TEMPLATE
════════════════════════════════════════
{_SCENE_TEMPLATE}

════════════════════════════════════════
  PRE-FLIGHT CHECKLIST (verify EVERY item)
════════════════════════════════════════
  □ scene.focus is MAX 6 words (no sentences)
  □ scene.text is MAX 1 short sentence (no paragraphs)
  □ Every actor has: id, type, role, x, y, size, color, animation
  □ molecule actors have moleculeType
  □ label actors have text (max 4 words) + fontSize
  □ arrow actors have angle + length + thickness
  □ sun actors have rays: true
  □ animations[] present in every scene with at least 1 entry
  □ animations[].from and animations[].to match actor ids in same scene
  □ startTime of each scene = sum of all previous scene durations
  □ script.duration = sum of ALL scene durations
  □ Scene count matches: {cfg['scene_count']}
  □ Actors per scene: {cfg['actors_per_scene']} — NOT more
  □ All x values: 60–740 | All y values: 60–540 | All sizes: 18–100
  □ No actor type outside the valid list
  □ No animation outside the valid list
  □ Student can understand the concept visually WITHOUT reading the text

Return ONLY valid JSON. No markdown. No explanation. No code fences.
The JSON root must have: title, cognitive_level, duration, scenes[]
Start immediately with the opening brace: {{
"""


def build_comprehensive_prompt(concept: str, cognitive_load: str = "medium") -> str:
    """
    Build a world-class educational prompt by first auto-detecting the domain,
    then calling the domain-aware prompt builder.
    """
    # Quick domain sniff (keyword-based, no API call needed)
    concept_lower = concept.lower()
    if any(k in concept_lower for k in ["photosynthesis", "cell", "leaf", "plant", "organism", "evolution", "dna", "gene"]):
        domain = "biology"
    elif any(k in concept_lower for k in ["water cycle", "rock cycle", "volcano", "earthquake", "erosion", "sediment", "weathering", "tectonic"]):
        domain = "earth_science"
    elif any(k in concept_lower for k in ["gravity", "force", "motion", "velocity", "acceleration", "energy", "wave", "light", "sound", "electricity"]):
        domain = "physics"
    elif any(k in concept_lower for k in ["atom", "molecule", "reaction", "bond", "element", "compound", "acid", "base", "oxidation"]):
        domain = "chemistry"
    elif any(k in concept_lower for k in ["planet", "solar", "star", "galaxy", "orbit", "moon", "comet", "asteroid", "nebula", "black hole"]):
        domain = "astronomy"
    else:
        domain = "generic"
    logger.info(f"[ai_generator] Domain sniffed: '{domain}' for concept '{concept}'")
    return build_prompt_for_load(concept, cognitive_load, domain=domain)


def build_prompt(concept: str) -> str:
    """Legacy alias."""
    return build_comprehensive_prompt(concept)


def clean_json_output(text: str) -> str:
    """Remove markdown, code blocks, and extract JSON."""
    if not text:
        return ""
    text = text.replace("```json", "").replace("```", "")
    for pattern in ["Here is the JSON:", "Here's the animation script:", "Animation script:", "JSON:"]:
        text = text.replace(pattern, "")
    start, end = text.find("{"), text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end].strip()
    return text.strip()


def analyze_concept(concept: str) -> dict:
    """Stage 1: Concept analysis – topic, level, domain, cognitive_load, keyIdeas (4–7)."""
    prompt = f"""
You are an educational concept analyst and cognitive load estimator.
Analyze the learning concept below and return a structured JSON object.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "topic": "<concise topic name, 2-5 words>",
  "level": "elementary" | "middle" | "high" | "university",
  "domain": "physics" | "biology" | "chemistry" | "astronomy" | "earth_science" | "math" | "generic",
  "cognitive_load": "low" | "medium" | "high",
  "keyIdeas": ["<step 1: cause or starting condition>", "<step 2: mechanism or process>", "<step 3: transformation or interaction>", "<step 4: output or result>", "<optional step 5+>"]
}}

Cognitive load estimation guide:
  low    = single object / single concept / young learner focus (e.g. "what is gravity?")
  medium = multi-step process or cause-effect chain (e.g. "photosynthesis", "water cycle")
  high   = complex system with feedback loops, equations, or multiple simultaneous processes

IMPORTANT for keyIdeas:
- Each idea should be a STEP in the process, not just a noun
- Include the CAUSE, the ACTION, and the EFFECT as separate steps
- 4 minimum, 7 maximum ideas

Concept: "{concept}"
"""
    try:
        raw = _generate_text(prompt, temperature=0.2, max_tokens=800)
        cleaned = clean_json_output(raw)
        analysis = json.loads(cleaned)
        topic = analysis.get("topic") or concept.strip()
        level = analysis.get("level") or "middle"
        domain = analysis.get("domain") or "generic"
        cognitive_load = analysis.get("cognitive_load") or "medium"
        key_ideas = analysis.get("keyIdeas") or [concept.strip()]
        if not isinstance(key_ideas, list):
            key_ideas = [str(key_ideas)]
        key_ideas = [str(i).strip() for i in key_ideas if str(i).strip()]
        if len(key_ideas) < 4:
            while len(key_ideas) < 4:
                key_ideas.append(key_ideas[-1] if key_ideas else concept.strip())
        key_ideas = key_ideas[:7]
        logger.info(f"[ai_generator] Concept analyzed: topic='{topic}', domain='{domain}', load='{cognitive_load}', ideas={len(key_ideas)}")
        return {"topic": topic, "level": level, "domain": domain, "cognitive_load": cognitive_load, "keyIdeas": key_ideas}
    except Exception as e:
        logger.error(f"[ai_generator] Error in analyze_concept: {e}")
        return {"topic": concept.strip(), "level": "middle", "domain": "generic", "cognitive_load": "medium", "keyIdeas": [concept.strip()]}


def plan_scenes_hybrid(concept_analysis: dict) -> list:
    """Stage 2 (Hybrid): AI scene planning – returns list of { scene, message, actors, actions }."""
    topic = concept_analysis.get("topic", "")
    domain = concept_analysis.get("domain", "generic")
    key_ideas = concept_analysis.get("keyIdeas", [])
    prompt = f"""
You are an educational animation story planner. Plan scenes for: "{topic}"
Return ONLY valid JSON:
{{
  "scenes": [
    {{ "scene": "scene_id", "message": "explanation", "actors": ["actor1", "actor2"], "actions": ["action1", "action2"] }}
  ]
}}
Key Ideas: {chr(10).join(f'- {i}' for i in key_ideas)}
Domain: {domain}
Use 4-7 scenes, 2-5 actors per scene. Simple verbs: erupt, flow, cool, erode, etc.
"""
    try:
        raw = _generate_text(prompt, temperature=0.3, max_tokens=1500)
        cleaned = clean_json_output(raw)
        result = json.loads(cleaned)
        scenes = result.get("scenes", [])
        validated = []
        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue
            scene_id = scene.get("scene") or f"scene_{i + 1}"
            message = scene.get("message") or (key_ideas[i] if i < len(key_ideas) else "")
            actors = scene.get("actors", [])
            actions = scene.get("actions", [])
            if not isinstance(actors, list):
                actors = [str(actors)] if actors else []
            if not isinstance(actions, list):
                actions = [str(actions)] if actions else []
            while len(actions) < len(actors):
                actions.append("idle")
            while len(actors) < len(actions):
                actors.append("label")
            validated.append({"scene": scene_id, "message": message, "actors": actors[:8], "actions": actions[:8]})
        if not validated:
            validated.append({"scene": "intro", "message": topic or "Explanation", "actors": ["label"], "actions": ["appear"]})
        return validated
    except Exception as e:
        print(f"Error in plan_scenes_hybrid: {e}")
        import traceback
        traceback.print_exc()
        return [{"scene": f"scene_{i+1}", "message": str(idea), "actors": ["label"], "actions": ["appear"]} for i, idea in enumerate(key_ideas[:7])]


def _generate_timeline_for_actor(actor_type: str, animation: str, x: int, y: int, appear_delay: int = 0) -> list:
    """Generate timeline steps for an actor (simplified)."""
    FADE_IN_DURATION = 600
    ACTION_DELAY = 800
    timeline = [
        {"at": appear_delay, "action": "appear", "alpha": 0.0},
        {"at": appear_delay + FADE_IN_DURATION, "action": "appear", "alpha": 1.0},
        {"at": appear_delay + FADE_IN_DURATION + ACTION_DELAY, "action": animation or "idle"},
        {"at": appear_delay + FADE_IN_DURATION + ACTION_DELAY + 1500, "action": "idle"},
    ]
    return timeline


def _pick_actors_for_idea(idea: str) -> list:
    """Create actors for an idea using KEYWORD_VISUAL_MAP + layout defaults."""
    idea_lower = idea.lower()
    actors = []
    SEQUENTIAL_DELAY = 1200
    primary_actors = []

    # Collect primary conceptual actors for this idea
    for keywords, actor_type, animation in KEYWORD_VISUAL_MAP:
        if any(k in idea_lower for k in keywords):
            if not any(a_type == actor_type for a_type, _ in primary_actors):
                primary_actors.append((actor_type, animation))

    for idx, (actor_type, animation) in enumerate(primary_actors):
        # Use layout engine to assign sensible x, y, size, color
        props = get_actor_properties(actor_type, {})
        x = props.get("x", 400)
        y = props.get("y", 300)
        color = props.get("color")
        appear_delay = idx * SEQUENTIAL_DELAY
        actor = {
            "type": actor_type,
            "x": x,
            "y": y,
            "animation": animation or "idle",
            "color": color,
            "count": 1,
        }
        actor["timeline"] = _generate_timeline_for_actor(actor_type, animation or "idle", x, y, appear_delay)
        actors.append(actor)

    if not actors:
        # Fallback: a label centered on screen, with layout-derived color and fontSize
        props = get_actor_properties("label", {"text": idea})
        x = props.get("x", 400)
        y = props.get("y", 300)
        color = props.get("color")
        actor = {
            "type": "label",
            "x": x,
            "y": y,
            "animation": "appear",
            "color": color,
            "count": 1,
        }
        # Preserve optional text/fontSize if frontend uses them
        if "text" in props:
            actor["text"] = props["text"]
        if "fontSize" in props:
            actor["fontSize"] = props["fontSize"]
        actor["timeline"] = _generate_timeline_for_actor("label", "appear", x, y, 0)
        actors.append(actor)

    return actors


def _infer_environment(analysis: dict, idea: str) -> str:
    """Infer environment hint for a scene."""
    domain = (analysis.get("domain") or "").lower()
    text = idea.lower()
    if domain == "astronomy" or any(k in text for k in ["space", "orbit", "moon", "planet", "galaxy", "universe"]):
        return "space"
    if domain in {"earth_science", "physics"} or any(k in text for k in ["ground", "earth", "mountain", "ocean", "volcano"]):
        return "earth"
    return "default"


def plan_scenes(analysis: dict) -> list:
    """Stage 2: Visual scene planning – key ideas to scenes with actors."""
    key_ideas = analysis.get("keyIdeas") or []
    if not isinstance(key_ideas, list):
        key_ideas = [str(key_ideas)]
    scenes = []
    for idx, idea in enumerate(key_ideas):
        idea_str = str(idea).strip()
        if not idea_str:
            continue
        scene_id = f"scene_{idx + 1}"
        actors = _pick_actors_for_idea(idea_str)
        scenes.append({"id": scene_id, "text": idea_str, "actors": actors, "environment": _infer_environment(analysis, idea_str)})
    if not scenes:
        scenes.append({"id": "scene_1", "text": analysis.get("topic") or "Explanation", "actors": _pick_actors_for_idea(analysis.get("topic") or ""), "environment": "default"})
    return scenes


def _build_script_from_scenes(concept: str, analysis: dict, planned_scenes: list) -> dict:
    """Stage 3: Build script with timing from planned scenes."""
    num_scenes = max(1, min(len(planned_scenes), 7))
    base_duration = 7000
    scenes_out = []
    current_start = 0
    for i in range(num_scenes):
        scene = planned_scenes[i]
        duration = base_duration
        scene_out = {"id": scene["id"], "startTime": current_start, "duration": duration, "text": scene["text"], "actors": scene["actors"]}
        if "environment" in scene:
            scene_out["environment"] = scene["environment"]
        scenes_out.append(scene_out)
        current_start += duration
    return {"title": analysis.get("topic") or concept.strip(), "duration": current_start, "scenes": scenes_out}


def _truncate_to_sentence(text: str, max_words: int = 20) -> str:
    """
    Enforce short, clean text. Returns the first sentence only,
    capped at max_words words. Strips HTML/newlines.
    """
    if not text:
        return ""
    # Collapse newlines and extra spaces
    text = " ".join(text.split())
    # Take only the first sentence
    for sep in (". ", "! ", "? "):
        idx = text.find(sep)
        if idx != -1:
            text = text[: idx + 1]
            break
    # Cap words
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]) + "."
    return text.strip()


def validate_json_script(script: dict) -> bool:  # noqa: C901
    """
    Validate, normalise, and auto-fix an animation script in-place.

    Accepts BOTH schema formats:
      v1 (old): scene has 'text', actors have no id/role, no top-level cognitive_level
      v2 (new): scene has 'focus' + 'text', actors have 'id'+'role', top-level 'cognitive_level',
                scenes have 'animations[]' array

    After this function the script is guaranteed to:
      - Have title, duration, scenes
      - Have scene.text (≤ 1 sentence, ≤ 20 words) derived from focus or truncated text
      - Have scene.focus (≤ 6 words) for the clean UI
      - Have all timing correct (cumulative startTime, duration sum)
      - Have valid actor types and animations
      - Have actor sizes clamped [10–120] and positions clamped to canvas
      - Preserve animations[] if present (validated against actor ids)
    """
    if not isinstance(script, dict):
        return False

    # ── Normalise root: handle 'cognitive_level' alias ────────────────────────
    if "cognitive_level" in script and "cognitive_load" not in script:
        script["cognitive_load"] = script["cognitive_level"]

    if not all(f in script for f in ["title", "duration", "scenes"]):
        return False
    if not isinstance(script["scenes"], list) or len(script["scenes"]) < 1:
        return False

    total_time = 0
    for i, scene in enumerate(script["scenes"]):
        if not isinstance(scene, dict):
            return False

        # ── Normalise scene text ───────────────────────────────────────────────
        # New format has 'focus' (≤6 words) + short 'text'. Old format has only 'text'.
        focus_raw = scene.get("focus", "")
        text_raw = scene.get("text", "")

        # Derive clean focus (≤6 words)
        if focus_raw:
            focus_words = focus_raw.split()
            scene["focus"] = " ".join(focus_words[:6])
        elif text_raw:
            # Derive focus from first few words of text
            scene["focus"] = " ".join(text_raw.split()[:6])
        else:
            scene["focus"] = f"Scene {i + 1}"

        # Derive clean text caption (≤1 sentence, ≤20 words)
        if text_raw:
            scene["text"] = _truncate_to_sentence(text_raw, max_words=20)
        elif focus_raw:
            # Promote focus to text if no text provided
            scene["text"] = focus_raw
        else:
            scene["text"] = scene["focus"]

        # ── Require scene structure ────────────────────────────────────────────
        if not all(f in scene for f in ["id", "duration", "actors"]):
            return False

        # ── Fix startTime (always recompute cumulatively) ──────────────────────
        scene["startTime"] = total_time
        total_time = scene["startTime"] + scene["duration"]

        actors = scene.get("actors", [])
        if not isinstance(actors, list) or len(actors) == 0:
            return False

        # Build actor id→type map for animations[] validation
        actor_id_map: dict[str, str] = {}

        for j, actor in enumerate(actors):
            if not isinstance(actor, dict):
                return False
            if not all(f in actor for f in ["type", "x", "y"]):
                return False

            # Auto-assign actor id if missing (new schema requirement)
            if "id" not in actor:
                actor["id"] = f"{actor['type']}_{j}"
            actor_id_map[actor["id"]] = actor["type"]

            # Default animation
            if "animation" not in actor and "timeline" not in actor:
                actor["animation"] = "idle"

            # Type normalisation / alias map
            if actor["type"] not in VALID_ACTOR_TYPES:
                _TYPE_MAP = {
                    "plants": "plant", "sunlight": "sun",
                    "water": "molecule", "h2o": "molecule",
                    "co2": "molecule", "oxygen": "molecule",
                    "carbon dioxide": "molecule",
                    "rock": "molecule", "magma": "molecule",
                    "lava": "molecule", "sediment": "molecule",
                    "wire": "line", "current": "line",
                    "field": "wave", "magnetic field": "wave",
                    "energy": "bolt", "force": "arrow",
                    "nucleus": "atom", "chloroplast": "cell",
                }
                orig_type = actor["type"].lower()
                if orig_type in _TYPE_MAP:
                    actor["type"] = _TYPE_MAP[orig_type]
                    if actor["type"] == "molecule":
                        _MOL_MAP = {
                            "water": "water", "h2o": "water",
                            "co2": "co2", "oxygen": "o2",
                            "carbon dioxide": "co2",
                            "rock": "rock", "magma": "magma",
                            "lava": "magma", "sediment": "sediment",
                        }
                        if "moleculeType" not in actor:
                            actor["moleculeType"] = _MOL_MAP.get(orig_type, "water")
                else:
                    return False  # Truly invalid type

            # Fix invalid animation
            if "animation" in actor and actor["animation"] not in VALID_ANIMATIONS:
                actor["animation"] = "idle"

            # Auto-fill missing size / color
            if "size" not in actor or "color" not in actor:
                props = get_actor_properties(actor["type"], {"moleculeType": actor.get("moleculeType")})
                if "size" not in actor and "size" in props:
                    actor["size"] = props["size"]
                if "color" not in actor and "color" in props:
                    actor["color"] = props["color"]

            # Clamp color strings ("yellow" → "#FFD700")
            _COLOR_NAMES = {
                "yellow": "#FFD700", "gold": "#FFD700",
                "blue": "#2196F3", "green": "#2E7D32",
                "red": "#F44336", "orange": "#FF9800",
                "grey": "#9E9E9E", "gray": "#9E9E9E",
                "purple": "#9C27B0", "white": "#FFFFFF",
                "black": "#212121",
            }
            if "color" in actor and not str(actor["color"]).startswith("#"):
                actor["color"] = _COLOR_NAMES.get(
                    str(actor["color"]).lower(), "#9E9E9E"
                )

            # Clamp size [10–120]
            if "size" in actor:
                actor["size"] = max(10, min(120, int(actor["size"])))

            # Clamp position to canvas
            if "x" in actor:
                actor["x"] = max(60, min(740, int(actor["x"])))
            if "y" in actor:
                actor["y"] = max(60, min(540, int(actor["y"])))

            # Normalise label text length (max 4 words)
            if actor["type"] == "label" and "text" in actor:
                label_words = str(actor["text"]).split()
                if len(label_words) > 6:
                    actor["text"] = " ".join(label_words[:6])

        # ── Validate animations[] (new schema) ────────────────────────────────
        if "animations" in scene:
            valid_anims = []
            for anim in scene["animations"]:
                if not isinstance(anim, dict):
                    continue
                from_id = anim.get("from", "")
                to_id = anim.get("to", "")
                anim_type = anim.get("type", "")
                # Only keep if both actor ids exist in this scene
                if from_id in actor_id_map and to_id in actor_id_map:
                    valid_anims.append(anim)
                elif from_id == to_id == "":
                    # Self-animation allowed (single actor transform)
                    valid_anims.append(anim)
            scene["animations"] = valid_anims

    # ── Fix root duration ──────────────────────────────────────────────────────
    if script["duration"] != total_time:
        script["duration"] = total_time
    return True


def _generate_animation_script_legacy(concept: str, cognitive_load: str = "medium", domain: str = "generic") -> Optional[dict]:
    """Comprehensive script generation via one Gemini call using world-class educational prompt."""
    try:
        logger.info(f"[ai_generator] Generating comprehensive script for '{concept}' (domain={domain}, load={cognitive_load})")
        prompt = build_prompt_for_load(concept, cognitive_load=cognitive_load, domain=domain)
        raw = _generate_text(prompt, temperature=0.3, max_tokens=6000)
        cleaned = clean_json_output(raw)
        script = json.loads(cleaned)
        if not validate_json_script(script):
            logger.warning("[ai_generator] Validation failed for generated comprehensive script.")
            return None
        logger.info("[ai_generator] Successfully generated and validated comprehensive script.")
        return script
    except Exception as e:
        logger.error(f"[ai_generator] Error generating script: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_animation_script(concept: str, use_comprehensive: bool = True) -> Optional[dict]:
    """
    Generate a world-class educational animation script.

    Flow:
      1. Analyze concept to detect domain + cognitive_load (fast pre-step, ~0.5s).
      2. Pass domain + load into the world-class educational prompt builder.
      3. Call Gemini with max_tokens=6000 for rich, multi-scene output.
      4. Validate output. Fall back to structured pipeline or hybrid as needed.
    """
    logger.info(f"[ai_generator] Starting AI generation for concept: '{concept}'")

    # Always detect domain + cognitive load first
    try:
        analysis = analyze_concept(concept)
        domain = analysis.get("domain", "generic")
        cognitive_load = analysis.get("cognitive_load", "medium")
        logger.info(f"[ai_generator] Detected domain='{domain}', cognitive_load='{cognitive_load}'")
    except Exception as e:
        logger.warning(f"[ai_generator] Concept analysis failed ({e}), using defaults.")
        analysis = {}
        domain = "generic"
        cognitive_load = "medium"

    # Primary: single comprehensive Gemini call with domain-aware world-class prompt
    if use_comprehensive:
        return _generate_animation_script_legacy(concept, cognitive_load=cognitive_load, domain=domain)

    # Secondary: structured pipeline (analyze -> plan_scenes -> build_script)
    try:
        logger.info("[ai_generator] Running structured pipeline (analyze -> plan -> build)")
        if not analysis.get("keyIdeas"):
            logger.warning("[ai_generator] No key ideas from analysis, falling back to comprehensive.")
            return _generate_animation_script_legacy(concept, cognitive_load=cognitive_load, domain=domain)

        planned_scenes = plan_scenes(analysis)
        if not planned_scenes:
            logger.warning("[ai_generator] Scene planning failed, falling back to comprehensive.")
            return _generate_animation_script_legacy(concept, cognitive_load=cognitive_load, domain=domain)

        script = _build_script_from_scenes(concept, analysis, planned_scenes)
        if not validate_json_script(script):
            logger.warning("[ai_generator] Script invalid, falling back to comprehensive.")
            return _generate_animation_script_legacy(concept, cognitive_load=cognitive_load, domain=domain)

        logger.info("[ai_generator] Successfully generated valid script via structured pipeline.")
        return script
    except Exception as e:
        logger.error(f"[ai_generator] Error in structured pipeline: {e}")
        return _generate_animation_script_legacy(concept, cognitive_load=cognitive_load, domain=domain)
