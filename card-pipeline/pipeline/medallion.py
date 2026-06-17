"""Medallion store (SQLite) — Bronze -> Silver -> Gold.

Bronze is the raw JSONL landing zone (the scraper's output). This module owns the
queryable layers the dashboard sits on:

  silver      every record after extraction + routing (in-flight working layer)
  gold        trusted, resolved canonical cards (later builds promote into this)
  quarantine  low-confidence records for human review (later builds)

Silver carries the full Tier-1 result plus ground truth (JSON), so the dashboard
can compute data-quality metrics and accuracy without re-running the pipeline.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import config as C

_SCHEMA = """
CREATE TABLE IF NOT EXISTS silver (
    listing_id           TEXT PRIMARY KEY,
    source               TEXT,
    scraped_at           TEXT,
    processed_at         TEXT,
    title                TEXT,
    description          TEXT,
    image_path           TEXT,
    tier_reached         TEXT,
    confidence           REAL,
    parallel_status      TEXT,
    decision             TEXT,   -- resolved | escalate
    next_tier            TEXT,   -- llm_text | cv_retrieval | NULL
    status               TEXT,   -- resolved_text | pending_*
    extracted_json       TEXT,
    ground_truth_json    TEXT,
    synthetic_difficulty TEXT
);
CREATE TABLE IF NOT EXISTS gold (
    listing_id        TEXT PRIMARY KEY,
    resolved_by       TEXT,      -- regex | llm_text | cv_retrieval | vision_llm | human
    canonical_json    TEXT,
    confidence        REAL,
    value_usd         REAL,
    promoted_at       TEXT
);
CREATE TABLE IF NOT EXISTS quarantine (
    listing_id   TEXT PRIMARY KEY,
    priority     REAL,           -- value * (1 - confidence)
    value_usd    REAL,
    confidence   REAL,
    best_guess_json TEXT,
    reason       TEXT,
    queued_at    TEXT
);
"""


def connect() -> sqlite3.Connection:
    C.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(C.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection, reset: bool = False) -> None:
    if reset:
        conn.executescript("DROP TABLE IF EXISTS silver;"
                           "DROP TABLE IF EXISTS gold;"
                           "DROP TABLE IF EXISTS quarantine;")
    conn.executescript(_SCHEMA)
    conn.commit()


def upsert_silver(conn: sqlite3.Connection, listing: dict, extraction: dict,
                  decision: dict) -> None:
    """Promote one record from Bronze into the Silver layer."""
    conn.execute(
        """INSERT OR REPLACE INTO silver (
            listing_id, source, scraped_at, processed_at, title, description,
            image_path, tier_reached, confidence, parallel_status, decision,
            next_tier, status, extracted_json, ground_truth_json, synthetic_difficulty
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            listing["listing_id"],
            listing.get("source"),
            listing.get("scraped_at"),
            datetime.now(timezone.utc).isoformat(),
            listing.get("title"),
            listing.get("description"),
            listing.get("image_path"),
            extraction["tier"],
            extraction["confidence"],
            extraction["parallel_status"],
            decision["decision"],
            decision["next_tier"],
            decision["status"],
            json.dumps(extraction["fields"], ensure_ascii=False),
            json.dumps(listing.get("ground_truth"), ensure_ascii=False),
            listing.get("_synthetic", {}).get("difficulty"),
        ),
    )
