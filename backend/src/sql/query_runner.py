from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

QUERY_FILENAMES = {
    "baseline_deviation": "baseline_deviation.sql",
    "fuel_trim_drift": "fuel_trim_drift.sql",
    "dtc_telemetry_correlation": "dtc_telemetry_correlation.sql",
    "session_baselines": "session_baselines.sql",
    "session_dtc_events": "session_dtc_events.sql",
    "session_health_score": "session_health_score.sql",
}

HEALTH_SCORE_CONFIG_KEYS = {
    "label",
    "metric_penalty_points",
    "pending_dtc_penalty",
    "stored_dtc_penalty",
    "permanent_dtc_penalty",
    "score_floor",
    "score_ceiling",
}


class QueryRunner:
    def __init__(self, query_dir: str | Path) -> None:
        self.query_dir = Path(query_dir)

    def run(
        self,
        conn: sqlite3.Connection,
        query_name: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        sql = self.load_sql(query_name)
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def load_sql(self, query_name: str) -> str:
        try:
            filename = QUERY_FILENAMES[query_name]
        except KeyError as exc:
            raise ValueError(f"Unknown Corvus query: {query_name}") from exc
        return (self.query_dir / filename).read_text(encoding="utf-8")


def load_health_score_config(config_path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    missing = HEALTH_SCORE_CONFIG_KEYS - raw.keys()
    if missing:
        raise ValueError(f"Health score config is missing: {sorted(missing)}")
    return {
        "score_basis": str(raw["label"]),
        "metric_penalty_points": float(raw["metric_penalty_points"]),
        "pending_dtc_penalty": float(raw["pending_dtc_penalty"]),
        "stored_dtc_penalty": float(raw["stored_dtc_penalty"]),
        "permanent_dtc_penalty": float(raw["permanent_dtc_penalty"]),
        "score_floor": float(raw["score_floor"]),
        "score_ceiling": float(raw["score_ceiling"]),
    }


def run_session_query(
    conn: sqlite3.Connection,
    query_dir: str | Path,
    query_name: str,
    session_id: int,
) -> list[dict[str, Any]]:
    runner = QueryRunner(query_dir)
    return runner.run(conn, query_name, {"session_id": session_id})


def run_session_health_score(
    conn: sqlite3.Connection,
    query_dir: str | Path,
    config_path: str | Path,
    session_id: int,
) -> dict[str, Any]:
    params = {"session_id": session_id, **load_health_score_config(config_path)}
    rows = QueryRunner(query_dir).run(conn, "session_health_score", params)
    if len(rows) != 1:
        raise ValueError(f"Expected one health score row, got {len(rows)}")
    return rows[0]
