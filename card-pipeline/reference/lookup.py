"""Runtime lookups against the reference dimensions.

`build_player_resolver(conn)` loads dim_player + player_alias once into memory and
returns a fast closure the extractor calls to validate/normalize a candidate name.

Resolution is **precision-first** — only:
  1. exact full-name match
  2. alias match (nicknames / spellings)
It trims trailing junk tokens, so "Victor Wembanyama PSA" still resolves to
"Victor Wembanyama" (the heuristic occasionally over-grabs — see NOTES §G), and it
folds accents so "Luka Doncic" matches "Luka Dončić".

We deliberately do NOT match on last name alone: that caused a cross-entity false
positive (NFL "J.J. McCarthy" matched NBA "Johnny McCarthy" because "McCarthy" was
unique in the NBA master). The correct production fix is **per-sport masters +
sport-scoped resolution** (NOTES §C); until then, strict matching keeps the trusted
layer clean.
"""
from __future__ import annotations

import sqlite3
import unicodedata


def _fold(s: str) -> str:
    """Lowercase + strip accents: 'Luka Dončić' -> 'luka doncic'."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def build_player_resolver(conn: sqlite3.Connection):
    """Return resolve(name) -> {"name", "player_id"} | None, or None if dim_player
    isn't seeded."""
    try:
        players = conn.execute(
            "SELECT player_id, full_name FROM dim_player"
        ).fetchall()
    except sqlite3.OperationalError:
        return None
    if not players:
        return None

    by_key: dict[str, dict] = {}  # folded full-name / alias -> player
    for player_id, full_name in players:
        by_key[_fold(full_name)] = {"name": full_name, "player_id": player_id}
    for alias, full_name, player_id in conn.execute(
        """SELECT a.alias, p.full_name, p.player_id
             FROM player_alias a JOIN dim_player p ON p.player_id = a.player_id"""
    ).fetchall():
        by_key[_fold(alias)] = {"name": full_name, "player_id": player_id}

    def resolve(candidate: str):
        if not candidate:
            return None
        toks = candidate.split()
        # Try the full candidate, then progressively shorter leading phrases
        # ("Victor Wembanyama PSA" -> "Victor Wembanyama").
        for k in range(len(toks), 0, -1):
            hit = by_key.get(_fold(" ".join(toks[:k])))
            if hit:
                return hit
        return None

    return resolve
