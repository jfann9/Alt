"""Tier 1 — regex / rule-based extraction (the free tier).

Parses a listing's title + description into structured card fields and a
confidence score, with NO model calls. Anything this tier resolves confidently
never costs an API dollar.

Design notes:
  * Confidence is a weighted sum of the *textual* fields we pin down
    (player, set, year, number, grade). It deliberately excludes the parallel.
  * The parallel/finish is a *visual* attribute — often unknowable from text —
    so we report it separately as `parallel_status`:
        named     a parallel keyword is present ("Silver", "Refractor", ...)
        uncertain the text signals an unstated parallel ("see photos", "?")
        base      no parallel mentioned and no uncertainty -> treat as base
    The router uses `parallel_status` to decide whether the image tiers are
    needed even when the textual confidence is high (the ambiguous-image case).
"""
from __future__ import annotations

import re

# --- Vocabularies (longest-first so multi-word brands match before their parts) ---
KNOWN_SETS = [
    "Topps Chrome", "Topps Heritage", "Bowman Chrome", "Panini Prizm",
    "Panini Select", "Panini Mosaic", "Panini Donruss Optic", "Panini Donruss",
    "Upper Deck", "Bowman", "Topps", "Select", "Mosaic", "Prizm", "Donruss",
    "Optic", "Fleer", "Score",
]
KNOWN_PARALLELS = [
    "Reverse Holo", "Red White Blue", "Cracked Ice", "Pink Ice", "Red Ice",
    "Orange Ice", "Green Ice", "Gold Sparkle", "Fast Break", "King Snake",
    "Refractor", "Silver", "Holo", "Mojo", "Ice", "Wave", "Disco", "Shimmer",
    "Sparkle", "Pulsar", "Velocity", "Hyper", "Genesis", "Camo",
    "Gold", "Green", "Pink", "Orange", "Purple", "Blue", "Red",
]
# Phrases that signal the seller is NOT pinning the parallel in text.
UNCERTAINTY_CUES = [
    "see photos", "see pics", "see pictures", "exact parallel", "parallel/finish",
    "which parallel", "exact finish", "pictured", "as shown", "as pictured",
]
# Tokens that are never a player's name — used to clean the name candidate.
_STOP_WORDS = {
    "rc", "rookie", "raw", "ungraded", "graded", "card", "lot", "ships", "ship",
    "top", "loader", "looks", "minty", "mint", "gem", "slabbed", "see", "photos",
    "photo", "pics", "exact", "parallel", "finish", "the", "in", "a", "of", "no",
}
_STOP_WORDS |= {w.lower() for s in KNOWN_SETS for w in s.split()}
_STOP_WORDS |= {w.lower() for p in KNOWN_PARALLELS for w in p.split()}

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_YEAR_APOS_RE = re.compile(r"'(\d{2})\b")
_GRADE_RE = re.compile(r"\b(PSA|BGS|BVG|SGC|CGC)\s?(10|9\.5|9|8\.5|8|7|6|5)\b", re.I)
_RAW_RE = re.compile(r"\b(raw|ungraded)\b", re.I)
_NUMBER_RE = re.compile(r"#\s?(\w+)|\bNo\.?\s?(\d+)\b", re.I)
_NAME_TOKEN_RE = re.compile(r"[A-Z][a-zA-Z'.-]+")

# Confidence weights for the textual fields (sum to 1.0).
_W = {"player": 0.35, "set": 0.20, "year": 0.15, "number": 0.15, "grade": 0.15}


def _find_year(text: str) -> int | None:
    m = _YEAR_RE.search(text)
    if m:
        return int(m.group(0))
    m = _YEAR_APOS_RE.search(text)  # "'25" -> 2025
    if m:
        return 2000 + int(m.group(1))
    return None


def _find_grade(text: str) -> str | None:
    m = _GRADE_RE.search(text)
    if m:
        return f"{m.group(1).upper()} {m.group(2)}"
    return None


def _grade_determined(text: str) -> bool:
    """A grade is 'determined' if a grade is named OR it's explicitly raw/ungraded."""
    return bool(_GRADE_RE.search(text) or _RAW_RE.search(text))


def _find_number(text: str) -> str | None:
    m = _NUMBER_RE.search(text)
    if m:
        return m.group(1) or m.group(2)
    return None


def _find_set(text: str) -> str | None:
    low = text.lower()
    for s in KNOWN_SETS:  # longest-first
        if s.lower() in low:
            return s
    return None


def _find_parallel(text: str) -> str | None:
    low = text.lower()
    for p in KNOWN_PARALLELS:  # longest-first
        if re.search(rf"\b{re.escape(p.lower())}\b", low):
            return p
    return None


def _parallel_status(text: str, parallel: str | None) -> str:
    if parallel:
        return "named"
    low = text.lower()
    if any(cue in low for cue in UNCERTAINTY_CUES):
        return "uncertain"
    return "base"


def _find_player(title: str, description: str) -> tuple[str | None, int]:
    """Heuristic name extraction: first run of capitalized non-stopword tokens.

    Returns (name_or_None, token_count). Token count drives partial confidence —
    a single token (just a last name) is worth half a full first+last match.
    """
    for source in (title, description):
        tokens = _NAME_TOKEN_RE.findall(source)
        run: list[str] = []
        for tok in tokens:
            if tok.lower() in _STOP_WORDS:
                if run:
                    break
                continue
            run.append(tok)
            if len(run) == 3:  # cap — names are 1-3 tokens here
                break
        if len(run) >= 2:
            return " ".join(run), len(run)
        if len(run) == 1 and source is description:  # fall back to a lone token
            return run[0], 1
    # last resort: a lone token from the title
    tokens = [t for t in _NAME_TOKEN_RE.findall(title) if t.lower() not in _STOP_WORDS]
    if tokens:
        return tokens[0], 1
    return None, 0


def _language(text: str) -> str:
    return "Japanese" if re.search(r"[぀-ヿ一-鿿]", text) else "English"


def extract(title: str, description: str = "") -> dict:
    """Run Tier-1 extraction. Returns fields, per-field hits, and confidence."""
    text = f"{title} {description}".strip()

    player, n_tokens = _find_player(title, description)
    year = _find_year(text)
    set_name = _find_set(text)
    number = _find_number(text)
    grade = _find_grade(text)
    parallel = _find_parallel(text)
    pstatus = _parallel_status(text, parallel)

    # Confidence = weighted coverage of textual fields.
    conf = 0.0
    if player:
        conf += _W["player"] * (1.0 if n_tokens >= 2 else 0.5)
    if set_name:
        conf += _W["set"]
    if year:
        conf += _W["year"]
    if number:
        conf += _W["number"]
    if _grade_determined(text):
        conf += _W["grade"]

    return {
        "fields": {
            "player": player,
            "set_name": set_name,
            "year": year,
            "card_number": number,
            "grade": grade,
            "parallel": parallel,
            "language": _language(text),
        },
        "parallel_status": pstatus,
        "confidence": round(conf, 3),
        "tier": "regex",
    }
