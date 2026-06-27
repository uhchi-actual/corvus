from __future__ import annotations

from pathlib import Path

import pytest

from src.ingest.database import connect_sqlite
from src.sql import run_session_health_score, run_session_query

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"
DB_PATH = ROOT / "data" / "seed" / "corvus.db"


def _public_session_id(conn, label: str) -> int:
    row = conn.execute(
        """
        SELECT session_id
        FROM drive_sessions
        WHERE source = 'public'
          AND notes LIKE ?
        LIMIT 1
        """,
        (f"%drive_label={label};%",),
    ).fetchone()
    assert row is not None, f"Missing public session for drive_label={label}"
    return int(row["session_id"])


@pytest.mark.skipif(not DB_PATH.exists(), reason="seed database missing")
def test_seat_leon_warm_drive_fits_warm_reference_band() -> None:
    with connect_sqlite(DB_PATH) as conn:
        session_id = _public_session_id(conn, "Traffic Jam Log")
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
        band = conn.execute(
            """
            SELECT context, healthy_min, healthy_max, source
            FROM baselines
            WHERE vehicle_id = (
              SELECT vehicle_id FROM drive_sessions WHERE session_id = ?
            )
              AND metric = 'coolant_temp_c'
            ORDER BY CASE context WHEN 'warm' THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        coolant = next(row for row in baseline if row["metric"] == "coolant_temp_c")

    assert band is not None
    assert band["context"] == "warm"
    assert band["source"] == "manual"
    assert coolant["pct_out_of_range"] <= 10.0


@pytest.mark.skipif(not DB_PATH.exists(), reason="seed database missing")
def test_seat_leon_cold_start_scores_below_warm_band() -> None:
    with connect_sqlite(DB_PATH) as conn:
        session_id = _public_session_id(conn, "Cold Start Log")
        health = run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id)
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
        coolant = next(row for row in baseline if row["metric"] == "coolant_temp_c")

    assert float(health["health_score"]) <= 90.0
    assert float(coolant["pct_out_of_range"]) >= 90.0


@pytest.mark.skipif(not DB_PATH.exists(), reason="seed database missing")
def test_ved_without_coolant_pid_uses_warming_fallback_band() -> None:
    with connect_sqlite(DB_PATH) as conn:
        ved = conn.execute(
            """
            SELECT session_id
            FROM drive_sessions s
            JOIN vehicles v ON v.vehicle_id = s.vehicle_id
            WHERE v.make = 'VED' AND s.source = 'public'
            ORDER BY session_id
            LIMIT 1
            """
        ).fetchone()
        assert ved is not None

        session_id = int(ved["session_id"])
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
        band = conn.execute(
            """
            SELECT context, source
            FROM baselines
            WHERE vehicle_id = (
              SELECT vehicle_id FROM drive_sessions WHERE session_id = ?
            )
              AND metric = 'coolant_temp_c'
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        coolant_samples = conn.execute(
            """
            SELECT COUNT(coolant_temp_c)
            FROM telemetry_samples
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()[0]

    assert band is not None
    assert band["context"] == "warm"
    assert band["source"] == "manual"
    assert coolant_samples == 0
    assert not any(row["metric"] == "coolant_temp_c" for row in baseline)
    assert any(row["metric"] == "engine_load_pct" for row in baseline)
