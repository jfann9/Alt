"""Seed dim_player (+ player_alias) from the nba_api static player list.

nba_api ships a bundled, offline list of every NBA/ABA player ever (~5,100 rows)
with a stable league id — ideal master data, no scraping or anti-bot to fight.
We also seed a small set of hand-curated nicknames to demonstrate the alias table
(the full alias corpus would grow via the human-review feedback loop, NOTES §C).

Run:  python -m reference.seed_players
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from reference.schema import create_reference_tables

# Nicknames / shorthand -> canonical full_name (as spelled in nba_api).
_NICKNAMES = {
    "Victor Wembanyama": ["Wemby"],
    "Giannis Antetokounmpo": ["Greek Freak"],
    "Stephen Curry": ["Steph", "Chef Curry"],
    "Kevin Durant": ["KD"],
    "LeBron James": ["King James", "Bron"],
    "Luka Dončić": ["Luka"],
    "Ja Morant": ["Ja"],
    "Chris Paul": ["CP3"],
    "Shai Gilgeous-Alexander": ["SGA"],
    "Anthony Edwards": ["Ant"],
}


def seed(conn: sqlite3.Connection) -> None:
    from nba_api.stats.static import players  # imported here so the pipeline
    # never hard-depends on nba_api at runtime — only seeding needs it.

    create_reference_tables(conn)
    conn.execute("DELETE FROM player_alias")
    conn.execute("DELETE FROM dim_player")

    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (p["id"], p["full_name"], p.get("first_name"), p.get("last_name"),
         1 if p.get("is_active") else 0, "basketball", "nba_api", now)
        for p in players.get_players()
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO dim_player
           (nba_person_id, full_name, first_name, last_name, is_active, sport, source, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )

    # Aliases (look up the surrogate player_id by full_name)
    alias_rows, missing = [], []
    for full_name, aliases in _NICKNAMES.items():
        r = conn.execute(
            "SELECT player_id FROM dim_player WHERE full_name = ?", (full_name,)
        ).fetchone()
        if not r:
            missing.append(full_name)
            continue
        for alias in aliases:
            alias_rows.append((r[0], alias, "nickname"))
    conn.executemany(
        "INSERT OR IGNORE INTO player_alias (player_id, alias, alias_type) VALUES (?,?,?)",
        alias_rows,
    )
    conn.commit()

    n_players = conn.execute("SELECT COUNT(*) FROM dim_player").fetchone()[0]
    n_active = conn.execute("SELECT COUNT(*) FROM dim_player WHERE is_active=1").fetchone()[0]
    n_alias = conn.execute("SELECT COUNT(*) FROM player_alias").fetchone()[0]
    print(f"dim_player seeded: {n_players} players ({n_active} active), {n_alias} aliases")
    if missing:
        print(f"  (nickname names not found in source, skipped: {missing})")


if __name__ == "__main__":
    conn = sqlite3.connect(C.DB_PATH)
    seed(conn)
    conn.close()
