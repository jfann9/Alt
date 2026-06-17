"""Seed all reference dimensions in one shot.

Run once before the pipeline:  python -m reference.seed_all
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C
from reference import seed_players, seed_vocabulary

if __name__ == "__main__":
    conn = sqlite3.connect(C.DB_PATH)
    seed_vocabulary.seed(conn)
    seed_players.seed(conn)
    conn.close()
    print(f"\nReference dimensions ready in {C.DB_PATH}")
