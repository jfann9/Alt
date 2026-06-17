"""Structured per-record event log (JSON Lines).

Every record's journey through the pipeline is appended here as discrete events
(`ingested`, `tier1_extract`, `routed`, ... later `cv_escalate`, `resolved`).
This is the simple, walkable audit trail — `jq` over it or replay it; it sits
alongside the queryable SQLite medallion tables, not instead of them.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import config as C


def reset() -> None:
    """Start a fresh log for a run (the SQLite tables hold durable state)."""
    C.EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    C.EVENTS_LOG.write_text("", encoding="utf-8")


def log(event: str, listing_id: str, **fields) -> None:
    """Append one event with a UTC timestamp."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "listing_id": listing_id,
        **fields,
    }
    with C.EVENTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
