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
def test_toyota_etios_uses_ved_light_band_and_scores_honestly() -> None:
    with connect_sqlite(DB_PATH) as conn:
        session_id = _public_session_id(conn, "City Commute Log")
        health = run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id)
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
        load_band = conn.execute(
            """
            SELECT healthy_min, healthy_max, source
            FROM baselines
            WHERE vehicle_id = (
              SELECT vehicle_id FROM drive_sessions WHERE session_id = ?
            )
              AND metric = 'engine_load_pct'
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        ltft = next((row for row in baseline if row["metric"] == "ltft_b1_pct"), None)
        stft = next((row for row in baseline if row["metric"] == "stft_b1_pct"), None)

    assert load_band is not None
    assert load_band["source"] == "ved-light"
    assert float(load_band["healthy_min"]) == pytest.approx(14.5)
    assert float(load_band["healthy_max"]) == pytest.approx(81.2)
    assert ltft is not None
    assert stft is not None
    score = float(health["health_score"])
    assert score < 100.0
    assert score >= 80.0
