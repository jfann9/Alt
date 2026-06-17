"""Seed dim_vocabulary from the curated lists in text_extract.

Migrates the in-code vocabulary into the reference table (the source of truth a
production system would edit without a deploy). Idempotent: clears and reloads.

Run:  python -m reference.seed_vocabulary
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from pipeline import text_extract as T
from reference.schema import create_reference_tables

# Map each curated list to its term_type in the dimension.
_GROUPS = [
    ("brand_set", T.DEFAULT_SETS),
    ("parallel", T.DEFAULT_PARALLELS),
    ("uncertainty_cue", T.DEFAULT_UNCERTAINTY),
    ("grade_company", T.DEFAULT_GRADE_COMPANIES),
    ("stop_word", sorted(T.BASE_STOP_WORDS)),
]


def seed(conn: sqlite3.Connection) -> None:
    create_reference_tables(conn)
    conn.execute("DELETE FROM dim_vocabulary")
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for term_type, terms in _GROUPS:
        for term in terms:
            rows.append((term_type, term, term, len(term), 1, "curated_seed", now))
    conn.executemany(
        """INSERT OR IGNORE INTO dim_vocabulary
           (term_type, term, canonical_term, match_priority, is_active, source, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    counts = dict(conn.execute(
        "SELECT term_type, COUNT(*) FROM dim_vocabulary GROUP BY term_type"
    ).fetchall())
    print(f"dim_vocabulary seeded: {counts} (total {sum(counts.values())})")


if __name__ == "__main__":
    conn = sqlite3.connect(C.DB_PATH)
    seed(conn)
    conn.close()
