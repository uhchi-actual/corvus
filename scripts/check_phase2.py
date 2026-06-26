from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.sql import run_session_health_score, run_session_query  # noqa: E402

DB_PATH = ROOT / "data" / "seed" / "corvus.db"
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"
QUERY_FILES = [
    "baseline_deviation.sql",
    "fuel_trim_drift.sql",
    "dtc_telemetry_correlation.sql",
    "session_health_score.sql",
]


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(DB_PATH)],
        check=True,
    )

    missing = [name for name in QUERY_FILES if not (QUERY_DIR / name).exists()]
    if missing:
        raise SystemExit(f"Missing Phase 2 query files: {missing}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id=1)
        drift = run_session_query(conn, QUERY_DIR, "fuel_trim_drift", session_id=1)
        correlation = run_session_query(conn, QUERY_DIR, "dtc_telemetry_correlation", session_id=1)
        health = run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id=1)

    if not baseline or baseline[0]["metric"] != "coolant_temp_c":
        raise SystemExit("Baseline deviation query did not return coolant facts")
    if len(drift) != 12 or "ltft_30s" not in drift[0]:
        raise SystemExit("Fuel-trim drift query did not return the expected rolling rows")
    if len(correlation) != 11 or correlation[0]["code"] != "P0171":
        raise SystemExit("DTC correlation query did not return the expected telemetry window")
    if health["score_basis"] != "directional editable scoring config":
        raise SystemExit("Health score query is not labeled as directional editable config")

    print("Phase 2 SQL contract OK")


if __name__ == "__main__":
    main()
