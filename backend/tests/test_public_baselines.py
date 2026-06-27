from __future__ import annotations

from pathlib import Path

import pytest

from src.ingest.database import connect_sqlite
from src.sql import run_session_query

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "data" / "queries"
DB_PATH = ROOT / "data" / "seed" / "corvus.db"


@pytest.mark.skipif(not DB_PATH.exists(), reason="seed database missing")
def test_seat_leon_baseline_fit_is_not_zeroed_by_warm_band() -> None:
    with connect_sqlite(DB_PATH) as conn:
        seat_leon = conn.execute(
            """
            SELECT session_id
            FROM drive_sessions s
            JOIN vehicles v ON v.vehicle_id = s.vehicle_id
            WHERE v.make = 'Seat' AND v.model = 'Leon' AND s.source = 'public'
            LIMIT 1
            """
        ).fetchone()
        assert seat_leon is not None

        session_id = int(seat_leon["session_id"])
        baseline = run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
        band = conn.execute(
            """
            SELECT context, healthy_min, healthy_max, source
            FROM baselines
            WHERE vehicle_id = (
              SELECT vehicle_id FROM drive_sessions WHERE session_id = ?
            )
              AND metric = 'coolant_temp_c'
            ORDER BY CASE context WHEN 'session' THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    assert band is not None
    assert band["context"] == "session"
    assert band["source"] == "derived"
    assert baseline[0]["pct_out_of_range"] < 5.0
