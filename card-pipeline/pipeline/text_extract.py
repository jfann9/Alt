"""Tier 1 — regex / rule-based extraction (the free tier).

Parses a listing's title + description into structured card fields and a
confidence score, with NO model calls. Anything this tier resolves confidently
never costs an API dollar.

Two upgrades over the first cut:
  * The vocabularies (sets, parallels, grade companies, cues, stop words) are
    loaded from the `dim_vocabulary` reference table when available, falling back
    to the in-file DEFAULTS below. This keeps reference data out of code (NOTES §C).
  * An optional `player_resolver` validates the extracted name against the
    `dim_player` master, normalizing it (and dropping junk like a leaked "PSA").

Confidence is a weighted sum of the *textual* fields we pin down (player, set,
year, number, grade). It excludes the parallel — a *visual* attribute reported
separately as `parallel_status` (named | uncertain | base) for the router.
"""
from __future__ import annotations

import re
import sqlite3

# --- DEFAULT vocabularies (fallback when the dim_vocabulary table isn't seeded) ---
DEFAULT_SETS = [
    "Topps Chrome", "Topps Heritage", "Bowman Chrome", "Panini Prizm",
    "Panini Select", "Panini Mosaic", "Panini Donruss Optic", "Panini Donruss",
    "Upper Deck", "Bowman", "Topps", "Select", "Mosaic", "Prizm", "Donruss",
    "Optic", "Fleer", "Score",
]
DEFAULT_PARALLELS = [
    "Reverse Holo", "Red White Blue", "Cracked Ice", "Pink Ice", "Red Ice",
    "Orange Ice", "Green Ice", "Gold Sparkle", "Fast Break", "King Snake",
    "Refractor", "Silver", "Holo", "Mojo", "Ice", "Wave", "Disco", "Shimmer",
    "Sparkle", "Pulsar", "Velocity", "Hyper", "Genesis", "Camo",
    "Gold", "Green", "Pink", "Orange", "Purple", "Blue", "Red",
]
DEFAULT_UNCERTAINTY = [
    "see photos", "see pics", "see pictures", "exact parallel", "parallel/finish",
    "which parallel", "exact finish", "pictured", "as shown", "as pictured",
]
DEFAULT_GRADE_COMPANIES = ["PSA", "BGS", "BVG", "SGC", "CGC"]
# Hand-listed fluff that is never a player name. Grade companies/words are here so
# the name heuristic can't glue "PSA" onto a player even without the resolver.
BASE_STOP_WORDS = {
    "rc", "rookie", "raw", "ungraded", "graded", "card", "lot", "ships", "ship",
    "top", "loader", "looks", "minty", "mint", "gem", "slabbed", "see", "photos",
    "photo", "pics", "exact", "parallel", "finish", "the", "in", "a", "of", "no",
    "psa", "bgs", "bvg", "sgc", "cgc",
}

# --- Static patterns (not vocabulary-driven) ---
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_YEAR_APOS_RE = re.compile(r"'(\d{2})\b")
_RAW_RE = re.compile(r"\b(raw|ungraded)\b", re.I)
_NUMBER_RE = re.compile(r"#\s?(\w+)|\bNo\.?\s?(\d+)\b", re.I)
_NAME_TOKEN_RE = re.compile(r"[A-Z][a-zA-Z'.-]+")

# Confidence weights for the textual fields (sum to 1.0).
_W = {"player": 0.35, "set": 0.20, "year": 0.15, "number": 0.15, "grade": 0.15}


# --------------------------------------------------------------------------- #
# Vocabulary assembly — one path for both DEFAULTS and the DB-loaded values
# --------------------------------------------------------------------------- #
def _assemble(sets, parallels, cues, grade_companies, base_stops) -> dict:
    sets = sorted(sets, key=len, reverse=True)        # longest-first matching
    parallels = sorted(parallels, key=len, reverse=True)
    stop = set(base_stops)
    stop |= {w.lower() for s in sets for w in s.split()}
    stop |= {w.lower() for p in parallels for w in p.split()}
    stop |= {g.lower() for g in grade_companies}
    companies = "|".join(re.escape(g) for g in grade_companies)
    grade_re = re.compile(rf"\b({companies})\s?(10|9\.5|9|8\.5|8|7|6|5)\b", re.I)
    return {"sets": sets, "parallels": parallels, "cues": cues,
            "stop_words": stop, "grade_re": grade_re}


_VOCAB = _assemble(DEFAULT_SETS, DEFAULT_PARALLELS, DEFAULT_UNCERTAINTY,
                   DEFAULT_GRADE_COMPANIES, BASE_STOP_WORDS)


def load_vocabularies_from_db(conn: sqlite3.Connection) -> bool:
    """Replace the active vocabulary with dim_vocabulary contents. Returns True
    if the table was present and populated; False -> the DEFAULTS stay in use."""
    global _VOCAB
    try:
        rows = conn.execute(
            "SELECT term_type, term FROM dim_vocabulary WHERE is_active = 1"
        ).fetchall()
    except sqlite3.OperationalError:
        return False  # table doesn't exist yet -> keep defaults
    if not rows:
        return False

    buckets: dict[str, list[str]] = {}
    for term_type, term in rows:
        buckets.setdefault(term_type, []).append(term)
    if not buckets.get("brand_set") or not buckets.get("parallel"):
        return False

    _VOCAB = _assemble(
        buckets.get("brand_set", []),
        buckets.get("parallel", []),
        buckets.get("uncertainty_cue", DEFAULT_UNCERTAINTY),
        buckets.get("grade_company", DEFAULT_GRADE_COMPANIES),
        buckets.get("stop_word", BASE_STOP_WORDS),
    )
    return True


# --------------------------------------------------------------------------- #
# Field finders (read the active _VOCAB)
# --------------------------------------------------------------------------- #
def _find_year(text: str) -> int | None:
    m = _YEAR_RE.search(text)
    if m:
        return int(m.group(0))
    m = _YEAR_APOS_RE.search(text)
    if m:
        return 2000 + int(m.group(1))
    return None


def _find_grade(text: str) -> str | None:
    m = _VOCAB["grade_re"].search(text)
    return f"{m.group(1).upper()} {m.group(2)}" if m else None


def _grade_determined(text: str) -> bool:
    return bool(_VOCAB["grade_re"].search(text) or _RAW_RE.search(text))


def _find_number(text: str) -> str | None:
    m = _NUMBER_RE.search(text)
    return (m.group(1) or m.group(2)) if m else None


def _find_set(text: str) -> str | None:
    low = text.lower()
    for s in _VOCAB["sets"]:
        if s.lower() in low:
            return s
    return None


def _find_parallel(text: str) -> str | None:
    low = text.lower()
    for p in _VOCAB["parallels"]:
        if re.search(rf"\b{re.escape(p.lower())}\b", low):
            return p
    return None


def _parallel_status(text: str, parallel: str | None) -> str:
    if parallel:
        return "named"
    low = text.lower()
    if any(cue in low for cue in _VOCAB["cues"]):
        return "uncertain"
    return "base"


def _candidate_name(title: str, description: str) -> tuple[str | None, int]:
    """Heuristic: first run of capitalized non-stopword tokens (see NOTES §G)."""
    stop = _VOCAB["stop_words"]
    for source in (title, description):
        run: list[str] = []
        for tok in _NAME_TOKEN_RE.findall(source):
            if tok.lower() in stop:
                if run:
                    break
                continue
            run.append(tok)
            if len(run) == 3:
                break
        if len(run) >= 2:
            return " ".join(run), len(run)
        if len(run) == 1 and source is description:
            return run[0], 1
    tokens = [t for t in _NAME_TOKEN_RE.findall(title) if t.lower() not in stop]
    return (tokens[0], 1) if tokens else (None, 0)


def _language(text: str) -> str:
    return "Japanese" if re.search(r"[぀-ヿ一-鿿]", text) else "English"


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def extract(title: str, description: str = "", player_resolver=None) -> dict:
    """Run Tier-1 extraction.

    player_resolver: optional callable(name:str) -> {"name", "player_id"} | None,
    typically built from the dim_player master. When it resolves a candidate, the
    name is normalized to canonical and treated as verified (full player weight).
    """
    text = f"{title} {description}".strip()

    candidate, n_tokens = _candidate_name(title, description)
    player, player_id, resolved = candidate, None, False
    if player_resolver and candidate:
        hit = player_resolver(candidate)
        if hit:
            player, player_id, resolved = hit["name"], hit["player_id"], True

    year = _find_year(text)
    set_name = _find_set(text)
    number = _find_number(text)
    grade = _find_grade(text)
    parallel = _find_parallel(text)
    pstatus = _parallel_status(text, parallel)

    conf = 0.0
    if player:
        # Verified-against-master OR a 2+ token guess earns full weight; a lone
        # unverified token earns half.
        conf += _W["player"] * (1.0 if (resolved or n_tokens >= 2) else 0.5)
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
            "player_id": player_id,
            "player_resolved": resolved,
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
