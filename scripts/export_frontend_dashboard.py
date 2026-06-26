from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.agent import LlmConfig, analyze_session  # noqa: E402
from src.ingest.database import connect_sqlite  # noqa: E402
from src.main import DISCLAIMER  # noqa: E402
from src.sql import run_session_health_score, run_session_query  # noqa: E402

DB_PATH = ROOT / "data" / "seed" / "corvus.db"
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"
OUT_PATH = ROOT / "frontend" / "src" / "data" / "dashboard.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static Corvus dashboard data.")
    parser.add_argument("--database", default=str(DB_PATH))
    parser.add_argument("--out", default=str(OUT_PATH))
    parser.add_argument("--refresh-db", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.database)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.refresh_db:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(db_path)],
            check=True,
        )

    with connect_sqlite(db_path) as conn:
        session_ids = _session_ids(conn)
        _prepare_dashboard_tables(conn, session_ids)
        focus_session_id = _focus_session_id(conn)
        _replace_seeded_finding(conn, focus_session_id)

    analysis = analyze_session(
        session_id=focus_session_id,
        database_path=db_path,
        query_dir=QUERY_DIR,
        config_path=CONFIG_PATH,
        disclaimer=DISCLAIMER,
        llm_config=LlmConfig(enabled=False, endpoint="", model="", api_key=""),
    )

    if analysis["status"] != "ok":
        raise SystemExit(f"Dashboard analysis failed: {analysis.get('error')}")

    with connect_sqlite(db_path) as conn:
        _prepare_dashboard_tables(conn, _session_ids(conn))
        payload = _dashboard_payload(conn, focus_session_id, analysis)

    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Frontend dashboard data written to {out_path}")


def _session_ids(conn: sqlite3.Connection) -> list[int]:
    return [
        int(row["session_id"])
        for row in conn.execute("SELECT session_id FROM drive_sessions ORDER BY session_id")
    ]


def _prepare_dashboard_tables(conn: sqlite3.Connection, session_ids: list[int]) -> None:
    conn.execute("DROP TABLE IF EXISTS temp.dashboard_health")
    conn.execute(
        """
        CREATE TEMP TABLE dashboard_health (
          session_id INTEGER,
          health_score REAL,
          metric_penalty_points REAL,
          dtc_penalty_points REAL,
          dtc_count INTEGER,
          telemetry_samples INTEGER,
          started_at TEXT,
          ended_at TEXT,
          score_basis TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO dashboard_health
          (session_id, health_score, metric_penalty_points, dtc_penalty_points,
           dtc_count, telemetry_samples, started_at, ended_at, score_basis)
        VALUES
          (:session_id, :health_score, :metric_penalty_points, :dtc_penalty_points,
           :dtc_count, :telemetry_samples, :started_at, :ended_at, :score_basis)
        """,
        [run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id) for session_id in session_ids],
    )

    conn.execute("DROP TABLE IF EXISTS temp.dashboard_baseline")
    conn.execute(
        """
        CREATE TEMP TABLE dashboard_baseline (
          session_id INTEGER,
          metric TEXT,
          context TEXT,
          sample_count INTEGER,
          out_of_range_samples INTEGER,
          pct_out_of_range REAL
        )
        """
    )
    baseline_rows = [
        {"session_id": session_id, **row}
        for session_id in session_ids
        for row in run_session_query(conn, QUERY_DIR, "baseline_deviation", session_id)
    ]
    conn.executemany(
        """
        INSERT INTO dashboard_baseline
          (session_id, metric, context, sample_count, out_of_range_samples, pct_out_of_range)
        VALUES
          (:session_id, :metric, :context, :sample_count, :out_of_range_samples, :pct_out_of_range)
        """,
        baseline_rows,
    )


def _focus_session_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT h.session_id
        FROM dashboard_health h
        JOIN drive_sessions s
          ON s.session_id = h.session_id
        WHERE s.source = 'public'
        ORDER BY h.health_score ASC, h.session_id ASC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise ValueError("No dashboard health rows available")
    return int(row["session_id"])


def _replace_seeded_finding(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute(
        """
        DELETE FROM findings
        WHERE session_id = ?
          AND metric_or_code = 'sql_analysis'
        """,
        (session_id,),
    )
    conn.commit()


def _dashboard_payload(
    conn: sqlite3.Connection,
    focus_session_id: int,
    analysis: dict[str, Any],
) -> dict[str, Any]:
    focus = _one(
        conn,
        """
        SELECT
          h.session_id,
          v.make || ' ' || v.model AS vehicle,
          s.source,
          s.notes AS notes,
          substr(
            s.notes,
            instr(s.notes, 'source_file=') + length('source_file='),
            instr(s.notes, '; drive_label=') - instr(s.notes, 'source_file=') - length('source_file=')
          ) AS source_file,
          substr(
            s.notes,
            instr(s.notes, 'drive_label=') + length('drive_label='),
            instr(s.notes, '; license=') - instr(s.notes, 'drive_label=') - length('drive_label=')
          ) AS drive_label,
          h.started_at,
          h.ended_at,
          printf('%.1f', h.health_score) AS health_score,
          printf('%.1f%%', h.health_score) AS health_score_width,
          printf('%.1f', h.metric_penalty_points) AS metric_penalty_points,
          printf('%.1f', h.dtc_penalty_points) AS dtc_penalty_points,
          CAST(h.dtc_count AS TEXT) AS dtc_count,
          CAST(h.telemetry_samples AS TEXT) AS telemetry_samples,
          h.score_basis,
          printf('%.1f', b.pct_out_of_range) AS pct_out_of_range,
          printf('%.1f%%', b.pct_out_of_range) AS baseline_width,
          CAST(b.out_of_range_samples AS TEXT) AS out_of_range_samples,
          CAST(b.sample_count AS TEXT) AS sample_count
        FROM dashboard_health h
        JOIN drive_sessions s
          ON s.session_id = h.session_id
        JOIN vehicles v
          ON v.vehicle_id = s.vehicle_id
        LEFT JOIN dashboard_baseline b
          ON b.session_id = h.session_id
        WHERE h.session_id = ?
        """,
        (focus_session_id,),
    )
    return {
        "project": "corvus",
        "version": "v1",
        "statement": "OBD-II telemetry analyzed in SQL",
        "focus": focus,
        "sessions": _rows(
            conn,
            """
            SELECT
              h.session_id,
              v.make || ' ' || v.model AS vehicle,
              s.source,
              s.notes AS notes,
              substr(
                s.notes,
                instr(s.notes, 'source_file=') + length('source_file='),
                instr(s.notes, '; drive_label=') - instr(s.notes, 'source_file=') - length('source_file=')
              ) AS source_file,
              substr(
                s.notes,
                instr(s.notes, 'drive_label=') + length('drive_label='),
                instr(s.notes, '; license=') - instr(s.notes, 'drive_label=') - length('drive_label=')
              ) AS drive_label,
              printf('%.1f', h.health_score) AS health_score,
              printf('%.1f%%', h.health_score) AS health_score_width,
              CAST(h.telemetry_samples AS TEXT) AS telemetry_samples,
              CAST(h.dtc_count AS TEXT) AS dtc_count,
              printf('%.1f', COALESCE(b.pct_out_of_range, 0.0)) AS pct_out_of_range,
              printf('%.1f%%', COALESCE(b.pct_out_of_range, 0.0)) AS baseline_width
            FROM dashboard_health h
            JOIN drive_sessions s
              ON s.session_id = h.session_id
            JOIN vehicles v
              ON v.vehicle_id = s.vehicle_id
            LEFT JOIN dashboard_baseline b
              ON b.session_id = h.session_id
            WHERE s.source = 'public'
            ORDER BY h.session_id
            """,
        ),
        "trend": _airflow_rows(conn, focus_session_id),
        "dtcEvidence": _dtc_rows(conn, focus_session_id),
        "finding": _finding(conn, focus_session_id),
        "agentTrace": analysis["agent_trace"],
        "agentTraceId": analysis["agent_trace_id"],
        "disclaimer": analysis["disclaimer"],
        "method": [
            "SQL computes score, trend, deviation, and diagnostic windows.",
            "Huginn reads the current session facts.",
            "Muninn recalls stored baselines.",
            "Trace IDs tie each finding to its evidence.",
        ],
        "workflow": [
            {
                "label": "Select drive",
                "body": "Use a logged session with known source and vehicle metadata.",
            },
            {
                "label": "Check score",
                "body": "Review directional penalties before reading the detailed rows.",
            },
            {
                "label": "Read evidence",
            "body": "Use airflow, baseline, and diagnostic windows to decide the next inspection.",
            },
            {
                "label": "Audit trace",
                "body": "Confirm which SQL rows Huginn and Muninn summarized.",
            },
        ],
        "dataSource": {
            "name": "KIT/RADAR Automotive OBD-II Dataset",
            "vehicle": "Seat Leon",
            "entries": [
                "2018-02-23_Seat_Leon_RT_RT_Frei_Beschleunigung.csv",
                "2018-03-21_Seat_Leon_KA_RT_Normal.csv",
                "2018-02-18_Seat_Leon_RT_KA_Stau.csv",
            ],
            "note": "Three real drive entries are used for the public dashboard. Public v1 charts mass air flow because these source files do not include fuel-trim fields.",
            "doi": "https://doi.org/10.35097/1130",
            "license": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/deed.en",
        },
        "inspiration": {
            "label": "F-Type P340 / Mustang GT 5.0",
            "image": "inspiration/f-type-mustang.jpg",
        },
    }


def _airflow_rows(conn: sqlite3.Connection, session_id: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        WITH airflow AS (
          SELECT
            ts,
            maf_gps,
            ROUND(
              AVG(maf_gps) OVER (
                ORDER BY ts
                ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
              ),
              2
            ) AS maf_30s
          FROM telemetry_samples
          WHERE session_id = ?
            AND maf_gps IS NOT NULL
        ),
        indexed AS (
          SELECT
            ts,
            maf_gps,
            maf_30s,
            ROW_NUMBER() OVER (ORDER BY ts) AS rn,
            COUNT(*) OVER () AS total_rows
          FROM airflow
        ),
        stepped AS (
          SELECT
            ts,
            maf_gps,
            maf_30s,
            rn,
            total_rows,
            CASE
              WHEN CAST(total_rows / 24 AS INTEGER) < 1 THEN 1
              ELSE CAST(total_rows / 24 AS INTEGER)
            END AS sample_step
          FROM indexed
        ),
        sampled AS (
          SELECT *
          FROM stepped
          WHERE rn = 1
             OR rn = total_rows
             OR ((rn - 1) % sample_step) = 0
        ),
        bounds AS (
          SELECT MAX(maf_30s) AS max_value
          FROM sampled
        )
        SELECT
          ts,
          printf('%.2f', maf_gps) AS maf_gps,
          printf('%.2f', maf_30s) AS maf_30s,
          printf(
            '%.1f%%',
            CASE
              WHEN bounds.max_value IS NULL OR bounds.max_value = 0 THEN 8.0
              ELSE 14.0 + 70.0 * maf_30s / bounds.max_value
            END
          ) AS height_pct
        FROM sampled
        CROSS JOIN bounds
        ORDER BY ts
        LIMIT 26
        """,
        (session_id,),
    )


def _dtc_rows(conn: sqlite3.Connection, session_id: int) -> list[dict[str, Any]]:
    conn.execute("DROP TABLE IF EXISTS temp.dashboard_dtc")
    conn.execute(
        """
        CREATE TEMP TABLE dashboard_dtc (
          code TEXT,
          status TEXT,
          description TEXT,
          fault_ts TEXT,
          ts TEXT,
          rpm REAL,
          engine_load_pct REAL,
          coolant_temp_c REAL
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO dashboard_dtc
          (code, status, description, fault_ts, ts, rpm, engine_load_pct, coolant_temp_c)
        VALUES
          (:code, :status, :description, :fault_ts, :ts, :rpm, :engine_load_pct, :coolant_temp_c)
        """,
        run_session_query(conn, QUERY_DIR, "dtc_telemetry_correlation", session_id),
    )
    rows = _rows(
        conn,
        """
        SELECT
          code,
          status,
          description,
          fault_ts,
          ts,
          printf('%.0f', rpm) AS rpm,
          printf('%.1f', engine_load_pct) AS engine_load_pct,
          printf('%.1f', coolant_temp_c) AS coolant_temp_c
        FROM dashboard_dtc
        ORDER BY ts
        LIMIT 6
        """,
    )
    if rows:
        return rows
    return [
        {
            "code": "none logged",
            "status": "none",
            "description": "No diagnostic trouble code was logged in this real public entry.",
            "fault_ts": "",
            "ts": "",
            "rpm": "n/a",
            "engine_load_pct": "n/a",
            "coolant_temp_c": "n/a",
        }
    ]


def _finding(conn: sqlite3.Connection, session_id: int) -> dict[str, Any]:
    return _one(
        conn,
        """
        SELECT
          severity,
          category,
          metric_or_code,
          expected_range,
          likely_cause,
          recommended_fix,
          agent_trace_id
        FROM findings
        WHERE session_id = ?
        ORDER BY finding_id DESC
        LIMIT 1
        """,
        (session_id,),
    )


def _rows(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise ValueError("Expected one dashboard row")
    return dict(row)


if __name__ == "__main__":
    main()
