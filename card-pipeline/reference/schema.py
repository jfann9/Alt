"""Reference / dimension schema (master data).

These tables hold the **reference data** the pipeline validates against — kept
out of application code so they can grow without a deploy (see NOTES.md §C).
They live in the same SQLite DB as the medallion tables so the dashboard can
join Silver/Gold against them, but they are seeded independently and are NOT
dropped by a normal pipeline run.

Modeling decisions worth defending in an interview:

* dim_player grain = ONE ROW PER PLAYER. The primary key is a **surrogate key**
  (`player_id`, an opaque auto integer). The league's own id (`nba_person_id`) is
  the **natural/business key**, stored as an attribute with a UNIQUE constraint.
  The player's NAME is just an attribute — names aren't unique, change over time,
  and have nicknames, so a name makes a poor key.

* A player's team and the year are NOT attributes of the player entity — a player
  spans many teams and seasons. That relationship has its own grain and lives in
  `bridge_player_season` (PK = composite `player_id + season + team_id`). This is
  the right home for "(year, team, player)". Keeping it separate is standard
  dimensional modeling (a player *dimension* vs. a roster *bridge/fact*).

* dim_vocabulary is a typed reference table (a "junk/reference dimension"): one
  surrogate key, a `term_type` discriminator, the literal `term`, and a
  `canonical_term`. It replaces the hardcoded Python lists in text_extract.
"""
from __future__ import annotations

import sqlite3

_DDL = """
-- Typed vocabulary reference (sets, parallels, grade companies, cues, stop words)
CREATE TABLE IF NOT EXISTS dim_vocabulary (
    term_id        INTEGER PRIMARY KEY AUTOINCREMENT,   -- surrogate key
    term_type      TEXT NOT NULL,   -- brand_set | parallel | grade_company | uncertainty_cue | stop_word
    term           TEXT NOT NULL,   -- the literal to match
    canonical_term TEXT,            -- normalized form (e.g. "prizm" -> "Panini Prizm")
    match_priority INTEGER DEFAULT 100,  -- higher = matched first (longest-first)
    is_active      INTEGER DEFAULT 1,
    source         TEXT,            -- provenance: curated_seed | checklist | feedback
    created_at     TEXT,
    UNIQUE (term_type, term)
);
CREATE INDEX IF NOT EXISTS ix_vocab_type ON dim_vocabulary (term_type, is_active);

-- Player dimension: one row per player. Surrogate PK + natural key attribute.
CREATE TABLE IF NOT EXISTS dim_player (
    player_id     INTEGER PRIMARY KEY AUTOINCREMENT,   -- surrogate key
    nba_person_id INTEGER UNIQUE,                      -- natural/business key (NBA's id)
    full_name     TEXT NOT NULL,
    first_name    TEXT,
    last_name     TEXT,
    is_active     INTEGER,          -- currently active in the league
    sport         TEXT DEFAULT 'basketball',
    source        TEXT,
    created_at    TEXT
);
CREATE INDEX IF NOT EXISTS ix_player_fullname ON dim_player (full_name);
CREATE INDEX IF NOT EXISTS ix_player_lastname ON dim_player (last_name);

-- Aliases: nicknames / spellings -> a player. 1-to-many child of dim_player.
CREATE TABLE IF NOT EXISTS player_alias (
    alias_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id  INTEGER NOT NULL REFERENCES dim_player (player_id),
    alias      TEXT NOT NULL,
    alias_type TEXT,               -- nickname | spelling | last_name
    UNIQUE (alias, player_id)
);
CREATE INDEX IF NOT EXISTS ix_alias_alias ON player_alias (alias);

-- Bridge: the proper home for (player, season, team). PK is the composite key.
-- Not seeded yet (would come from roster data, e.g. nba_api CommonTeamRoster);
-- created here to make the model explicit. team_id would FK to a dim_team.
CREATE TABLE IF NOT EXISTS bridge_player_season (
    player_id INTEGER NOT NULL REFERENCES dim_player (player_id),
    season    TEXT NOT NULL,       -- e.g. '2023-24'
    team_id   INTEGER,             -- FK -> dim_team (future)
    PRIMARY KEY (player_id, season, team_id)
);
"""


def create_reference_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(_DDL)
    conn.commit()
