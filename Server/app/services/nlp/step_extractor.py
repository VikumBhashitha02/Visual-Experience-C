"""
Step Extractor — Grade 6 Visual Learning Pipeline

Converts 100–350 word educational text into 4–6 ordered, simplified steps
suitable for Grade 6 students.

Pipeline:
  Phase 1: Rule-based sentence scoring (TF-IDF + position + causal markers)
  Phase 2: Sentence simplification (rule-based, no LLM required)
  Phase 3: LLM refinement (optional — only called if USE_LLM=True)
  Phase 4: Output clamping (max 5 steps, min words enforced)

Public API:
  extract_steps(text, max_steps=5, use_llm=False) -> list[str]
  build_step_extraction_prompt(text, max_steps=5) -> str
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Grade 6 word simplifier ─────────────────────────────────────────────────
# Maps complex academic/scientific words to simpler equivalents.
# Keeps scientific nouns (photosynthesis, gravity) intact — only replaces
# structural/academic words that confuse young readers.

_SIMPLIFY_MAP: dict[str, str] = {
    # Academic verbs → plain verbs
    "absorbs": "takes in",
    "absorb": "take in",
    "emits": "sends out",
    "emit": "send out",
    "converts": "changes",
    "convert": "change",
    "releases": "lets out",
    "release": "let out",
    "produces": "makes",
    "produce": "make",
    "enables": "allows",
    "enable": "allow",
    "utilises": "uses",
    "utilizes": "uses",
    "obtains": "gets",
    "obtain": "get",
    "requires": "needs",
    "require": "need",
    "demonstrates": "shows",
    "demonstrate": "show",
    "generates": "creates",
    "generate": "create",
    "accelerates": "speeds up",
    "accelerate": "speed up",
    "decelerates": "slows down",
    "decelerate": "slow down",
    "transforms": "changes into",
    "transform": "change into",
    # Academic adjectives/nouns → plain equivalents
    "sufficient": "enough",
    "primary": "main",
    "fundamental": "basic",
    "approximately": "about",
    "therefore": "so",
    "consequently": "as a result",
    "subsequently": "then",
    "furthermore": "also",
    "nevertheless": "but",
    "simultaneously": "at the same time",
    "perpendicular": "at a right angle",
    "perpendicular to": "at a right angle to",
    "proportional to": "depends on",
    "inversely": "the opposite way",
    "horizontal": "flat",
    "vertical": "straight up",
    "atmosphere": "air around Earth",
    "organisms": "living things",
    "organism": "living thing",
    "nucleus": "center",
    "nutrients": "food minerals",
}

# Causal / process marker words — sentences containing these rank higher
# because they describe WHAT HAPPENS, which maps to animation steps.
_CAUSAL_MARKERS: list[str] = [
    "because", "causes", "results in", "leads to", "produces",
    "when", "after", "before", "then", "next", "finally",
    "so that", "in order to", "allows", "enables", "converts",
    "absorbs", "releases", "transforms", "moves", "pulls", "pushes",
    "rises", "falls", "flows", "enters", "exits", "forms",
]

# Step-starter phrases that make the output feel like instructions.
_STEP_PREFIXES: list[str] = [
    "First,", "Next,", "Then,", "After that,", "Finally,"
]


# ─── Phase 1: Sentence extraction + scoring ──────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex (no spaCy dependency here)."""
    # Split on . ! ? followed by whitespace or end-of-string
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = []
    for s in raw:
        s = s.strip()
        if len(s.split()) >= 4:  # skip fragments shorter than 4 words
            sentences.append(s)
    return sentences


def _score_sentence(sentence: str, position: int, total: int) -> float:
    """
    Score a sentence for its 'teaching value'.

    Scoring factors:
      +0.4   if sentence contains a causal/process marker word
      +0.3   if sentence is in the first third of the text (topic introduction)
      +0.15  if sentence is in the last quarter (conclusion / summary)
      -0.2   if sentence is longer than 35 words (too complex for Grade 6)
      +0.1   if sentence length is 8–20 words (ideal length for a step)
    """
    s_lower = sentence.lower()
    word_count = len(sentence.split())
    score = 0.0

    # Causal / process marker bonus
    for marker in _CAUSAL_MARKERS:
        if marker in s_lower:
            score += 0.4
            break  # only count once per sentence

    # Position bonus — first third of text usually introduces key ideas
    relative_pos = position / max(total - 1, 1)
    if relative_pos <= 0.33:
        score += 0.3
    elif relative_pos >= 0.75:
        score += 0.15

    # Word count bonuses / penalties
    if word_count > 35:
        score -= 0.2
    elif 8 <= word_count <= 20:
        score += 0.1

    return score


def _select_top_sentences(text: str, max_steps: int) -> list[str]:
    """
    Score all sentences and return the top-scoring ones IN ORIGINAL ORDER.
    Preserving original order matters — it keeps the logical progression.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    total = len(sentences)
    scored = [
        (i, s, _score_sentence(s, i, total))
        for i, s in enumerate(sentences)
    ]

    # Sort by score descending, pick top max_steps
    top_indices = sorted(
        scored, key=lambda x: x[2], reverse=True
    )[:max_steps]

    # Re-sort by original position to preserve logical order
    top_indices_sorted = sorted(top_indices, key=lambda x: x[0])

    return [s for _, s, _ in top_indices_sorted]


# ─── Phase 2: Rule-based sentence simplification ─────────────────────────────

def _simplify_sentence(sentence: str) -> str:
    """
    Apply word-level simplification rules to a single sentence.

    Rules applied in order:
    1. Replace academic words using _SIMPLIFY_MAP
    2. Strip parenthetical clauses — e.g. "(which is also called X)"
    3. Remove trailing subordinate clauses after semicolons
    4. Capitalise first letter, ensure single terminal period
    """
    result = sentence.strip()

    # 1. Word replacement (case-insensitive, whole-word matching)
    for complex_word, simple_word in _SIMPLIFY_MAP.items():
        pattern = re.compile(r'\b' + re.escape(complex_word) + r'\b', re.IGNORECASE)
        result = pattern.sub(simple_word, result)

    # 2. Remove parenthetical clauses e.g. "(also known as X)"
    result = re.sub(r'\s*\([^)]{1,60}\)', '', result)

    # 3. Trim at semicolon — keep only the main clause
    if ';' in result:
        result = result.split(';')[0].strip()

    # 4. Trim very long sentences: cut after the first full clause
    #    (identified by a comma after 10+ words)
    words = result.split()
    if len(words) > 28:
        # Find a natural comma cut point
        cut_match = re.search(r'^(.{60,}?),\s', result)
        if cut_match:
            result = cut_match.group(1).strip()

    # 5. Ensure clean capitalisation and single period
    if result:
        result = result[0].upper() + result[1:]
        result = result.rstrip('.!?') + '.'

    return result


def _add_step_prefixes(steps: list[str]) -> list[str]:
    """Prepend 'First,', 'Next,', 'Then,' etc. to each step."""
    prefixed = []
    for i, step in enumerate(steps):
        if i < len(_STEP_PREFIXES):
            prefix = _STEP_PREFIXES[i]
        else:
            prefix = "Also,"
        # Remove leading capital and re-attach with prefix
        if step and step[0].isupper():
            step_body = step[0].lower() + step[1:]
        else:
            step_body = step
        prefixed.append(f"{prefix} {step_body}")
    return prefixed


# ─── Phase 3: LLM refinement prompt ─────────────────────────────────────────

def build_step_extraction_prompt(text: str, max_steps: int = 5) -> str:
    """
    Build a Gemini prompt for LLM-enhanced step extraction.

    Use this when rule-based output is not satisfactory, or for higher-quality
    production results. Pass the returned string to generate_text().

    Returns:
        Prompt string ready to send to Gemini.
    """
    return f"""You are a Grade 6 science teacher who creates simple step-by-step explanations.

Your task: Read the science text below and extract exactly {max_steps} key steps.

STRICT RULES:
1. Return ONLY a JSON array of {max_steps} strings. Nothing else.
2. Each step = ONE simple sentence. Max 15 words per step.
3. Use everyday language a 12-year-old understands.
4. Keep scientific nouns (gravity, photosynthesis, atom) — only simplify structure.
5. Steps must follow a logical order: cause first, effect last.
6. Start each step with an action word: "The sun...", "Water moves...", "Leaves make..."
7. Do NOT include formulas, numbers, or technical symbols.
8. Do NOT explain — just describe what happens, simply.

BAD step example:  "The process of photosynthesis involves the absorption of solar radiation."
GOOD step example: "The leaf takes in sunlight from the sun."

Science text:
\"\"\"{text.strip()}\"\"\"

Return ONLY this JSON format, nothing else:
["step 1 here", "step 2 here", "step 3 here", "step 4 here", "step 5 here"]
"""


# ─── Phase 4: LLM response parser ───────────────────────────────────────────

def _parse_llm_steps(llm_output: str, max_steps: int) -> Optional[list[str]]:
    """
    Parse the LLM JSON array response into a clean Python list.
    Returns None if parsing fails (caller falls back to rule-based output).
    """
    import json

    text = llm_output.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Find the JSON array
    start = text.find('[')
    end = text.rfind(']') + 1
    if start == -1 or end <= start:
        return None

    try:
        steps = json.loads(text[start:end])
        if not isinstance(steps, list):
            return None
        # Sanitise each step
        clean = [str(s).strip() for s in steps if str(s).strip()]
        clean = clean[:max_steps]
        return clean if clean else None
    except (json.JSONDecodeError, ValueError):
        return None


# ─── Public API ──────────────────────────────────────────────────────────────

def extract_steps(
    text: str,
    max_steps: int = 5,
    use_llm: bool = False,
    add_prefixes: bool = True,
) -> list[str]:
    """
    Convert 100–350 word educational text into max_steps simple steps for Grade 6.

    Args:
        text:         Raw educational text (100–350 words recommended).
        max_steps:    Maximum number of steps to return (default 5, max 6).
        use_llm:      If True, calls Gemini to improve step quality.
                      Requires GEMINI_API_KEY in .env. Falls back to
                      rule-based output if LLM fails.
        add_prefixes: If True, prepends "First,", "Next,", etc. to each step.

    Returns:
        List of simplified step strings, ordered logically.
        Always returns between 1 and max_steps items.

    Example:
        >>> steps = extract_steps(text, max_steps=5)
        >>> print(steps)
        [
          "First, the sun sends out light energy.",
          "Next, the leaf takes in the sunlight.",
          "Then, the root takes in water from the soil.",
          "After that, the leaf changes sunlight and water into food.",
          "Finally, the leaf lets out oxygen into the air."
        ]
    """
    max_steps = min(max(1, max_steps), 6)  # clamp to 1–6

    if not text or not text.strip():
        logger.warning("[step_extractor] Empty text input.")
        return ["The concept could not be broken into steps."]

    word_count = len(text.split())
    if word_count < 20:
        logger.warning("[step_extractor] Text too short (%d words). Returning as single step.", word_count)
        return [_simplify_sentence(text.strip())]

    # ── Phase 1: Select most important sentences ──
    selected = _select_top_sentences(text, max_steps)
    if not selected:
        logger.warning("[step_extractor] No sentences extracted. Returning fallback.")
        return [_simplify_sentence(text.strip()[:200])]

    # ── Phase 2: Rule-based simplification ──
    rule_based_steps = [_simplify_sentence(s) for s in selected]
    rule_based_steps = [s for s in rule_based_steps if s.strip()]

    # ── Phase 3: Optional LLM enhancement ──
    if use_llm:
        try:
            from app.services.nlp.text_llm_client import generate_text
            prompt = build_step_extraction_prompt(text, max_steps)
            llm_raw = generate_text(prompt, temperature=0.2, max_tokens=600)
            llm_steps = _parse_llm_steps(llm_raw, max_steps)
            if llm_steps:
                logger.info("[step_extractor] LLM produced %d steps.", len(llm_steps))
                final_steps = llm_steps
            else:
                logger.warning("[step_extractor] LLM parse failed — using rule-based steps.")
                final_steps = rule_based_steps
        except Exception as e:
            logger.error("[step_extractor] LLM call failed (%s) — using rule-based steps.", e)
            final_steps = rule_based_steps
    else:
        final_steps = rule_based_steps

    # ── Phase 4: Add step prefixes and return ──
    if add_prefixes:
        final_steps = _add_step_prefixes(final_steps)

    logger.info("[step_extractor] Extracted %d steps from %d-word text.", len(final_steps), word_count)
    return final_steps
