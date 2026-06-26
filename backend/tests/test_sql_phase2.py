from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

from src.sql import QueryRunner, run_session_health_score, run_session_query

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"


def _seeded_db(tmp_path: Path) -> Path:
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


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def test_showcase_queries_return_seeded_session_facts(tmp_path: Path) -> None:
    db_path = _seeded_db(tmp_path)
    with _connect(db_path) as conn:
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id=1)
        drift = run_session_query(conn, QUERY_DIR, "fuel_trim_drift", session_id=1)
        correlation = run_session_query(
            conn,
            QUERY_DIR,
            "dtc_telemetry_correlation",
            session_id=1,
        )

    assert baseline[0]["metric"] == "coolant_temp_c"
    assert baseline[0]["sample_count"] == 12
    assert drift[0]["ltft_30s"] == 4.1
    assert drift[-1]["ltft_30s"] > drift[0]["ltft_30s"]
    assert {row["code"] for row in correlation} == {"P0171"}
    assert len(correlation) == 11


def test_session_health_score_is_sql_computed_and_directional(tmp_path: Path) -> None:
    db_path = _seeded_db(tmp_path)
    with _connect(db_path) as conn:
        score_one = run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id=1)
        score_two = run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id=2)

    assert 0 <= score_one["health_score"] <= 100
    assert 0 <= score_two["health_score"] <= 100
    assert score_one["score_basis"] == "directional editable scoring config"
    assert score_two["score_basis"] == "directional editable scoring config"
    assert score_one["telemetry_samples"] == 12
    assert score_two["dtc_count"] == 1


def test_query_runner_rejects_unknown_query() -> None:
    runner = QueryRunner(QUERY_DIR)

    try:
        runner.load_sql("made_up_query")
    except ValueError as exc:
        assert "Unknown Corvus query" in str(exc)
    else:
        raise AssertionError("QueryRunner accepted an unknown query")
