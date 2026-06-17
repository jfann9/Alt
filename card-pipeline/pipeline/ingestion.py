"""Ingestion — read the Bronze landing file and hand validated listings forward.

Bronze is the immutable raw layer (`data/bronze/listings_raw.jsonl`). This module
does the minimum a landing-zone reader should: load, validate the shape, and drop
(with a count) anything malformed — it does not clean or enrich.
"""
from __future__ import annotations

import json
from pathlib import Path

import config as C

REQUIRED = ("listing_id", "title")


def load_listings(path: Path | None = None) -> list[dict]:
    """Return well-formed Bronze listings; warn on any skipped rows."""
    path = path or C.LISTINGS_RAW
    if not path.exists():
        raise FileNotFoundError(
            f"Bronze file not found: {path}\nRun the scraper first: "
            f"python -m scraper.sportscardspro"
        )

    good, skipped = [], 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if all(rec.get(k) for k in REQUIRED):
                good.append(rec)
            else:
                skipped += 1

    if skipped:
        print(f"  ingestion: skipped {skipped} malformed/incomplete rows")
    return good
