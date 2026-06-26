from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"


def seeded_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "corvus.db"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "seed_database.py"),
            "--database",
            str(db_path),
        ],
        check=True,
        cwd=ROOT,
    )
    return db_path


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
