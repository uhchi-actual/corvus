from __future__ import annotations

import argparse
import csv
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.ingest.database import connect_sqlite  # noqa: E402
from src.sql import run_session_health_score, run_session_query  # noqa: E402

DB_PATH = ROOT / "data" / "seed" / "corvus.db"
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"
EXPORT_DIR = ROOT / "powerbi" / "export"
SCREENSHOT_DIR = ROOT / "powerbi" / "screenshots"

UHCHI_RED = "#cc2936"
UHCHI_TEAL = "#1f7f78"
UHCHI_DARK = "#2d2d2d"
OFF_WHITE = "#eadbc6"
PANEL = "#242424"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Corvus SQLite data for Power BI.")
    parser.add_argument("--database", default=str(DB_PATH))
    parser.add_argument("--export-dir", default=str(EXPORT_DIR))
    parser.add_argument("--screenshots-dir", default=str(SCREENSHOT_DIR))
    parser.add_argument("--refresh-db", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.database)
    export_dir = Path(args.export_dir)
    screenshots_dir = Path(args.screenshots_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    if args.refresh_db:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(db_path)],
            check=True,
        )

    with connect_sqlite(db_path) as conn:
        _export_query(conn, export_dir / "vehicles.csv", "SELECT * FROM vehicles ORDER BY vehicle_id")
        _export_query(
            conn,
            export_dir / "drive_sessions.csv",
            """
            SELECT
              s.session_id,
              s.vehicle_id,
              v.make,
              v.model,
              v.year,
              v.engine,
              s.started_at,
              s.ended_at,
              s.source,
              s.ambient_c,
              s.notes
            FROM drive_sessions s
            JOIN vehicles v
              ON v.vehicle_id = s.vehicle_id
            ORDER BY s.session_id
            """,
        )
        _export_query(
            conn,
            export_dir / "telemetry_samples.csv",
            "SELECT * FROM telemetry_samples ORDER BY session_id, ts, sample_id",
        )
        _export_query(conn, export_dir / "dtc_events.csv", "SELECT * FROM dtc_events ORDER BY dtc_id")
        _export_query(conn, export_dir / "baselines.csv", "SELECT * FROM baselines ORDER BY baseline_id")
        _export_query(
            conn,
            export_dir / "session_overview.csv",
            """
            SELECT
              s.session_id,
              v.make,
              v.model,
              s.source,
              s.started_at,
              s.ended_at,
              COUNT(t.sample_id) AS telemetry_samples,
              COUNT(DISTINCT d.dtc_id) AS dtc_events
            FROM drive_sessions s
            JOIN vehicles v
              ON v.vehicle_id = s.vehicle_id
            LEFT JOIN telemetry_samples t
              ON t.session_id = s.session_id
            LEFT JOIN dtc_events d
              ON d.session_id = s.session_id
            GROUP BY s.session_id, v.make, v.model, s.source, s.started_at, s.ended_at
            ORDER BY s.session_id
            """,
        )

        session_ids = [
            int(row["session_id"])
            for row in conn.execute("SELECT session_id FROM drive_sessions ORDER BY session_id")
        ]
        _export_rows(
            export_dir / "health_scores.csv",
            [run_session_health_score(conn, QUERY_DIR, CONFIG_PATH, session_id) for session_id in session_ids],
        )
        _export_rows(
            export_dir / "baseline_deviation.csv",
            _query_all_sessions(conn, session_ids, "baseline_deviation"),
        )
        _export_rows(
            export_dir / "fuel_trim_drift.csv",
            _query_all_sessions(conn, session_ids, "fuel_trim_drift"),
        )
        _export_rows(
            export_dir / "dtc_telemetry_correlation.csv",
            _query_all_sessions(conn, session_ids, "dtc_telemetry_correlation"),
        )
        _export_query(
            conn,
            export_dir / "findings.csv",
            "SELECT * FROM findings ORDER BY finding_id",
        )

    _render_report_previews(export_dir, screenshots_dir)
    print(f"Power BI exports written to {export_dir}")
    print(f"Report preview screenshots written to {screenshots_dir}")


def _query_all_sessions(
    conn: sqlite3.Connection,
    session_ids: list[int],
    query_name: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for session_id in session_ids:
        for row in run_session_query(conn, QUERY_DIR, query_name, session_id):
            rows.append({"session_id": session_id, **row})
    return rows


def _export_query(conn: sqlite3.Connection, path: Path, sql: str) -> None:
    cursor = conn.execute(sql)
    fieldnames = [column[0] for column in cursor.description]
    rows = [dict(row) for row in cursor]
    _export_rows(path, rows, fieldnames)


def _export_rows(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str] | None = None,
) -> None:
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _render_report_previews(export_dir: Path, screenshots_dir: Path) -> None:
    overview_rows = _read_csv(export_dir / "session_overview.csv")
    health_rows = _read_csv(export_dir / "health_scores.csv")
    dtc_rows = _read_csv(export_dir / "dtc_telemetry_correlation.csv")
    drift_rows = _read_csv(export_dir / "fuel_trim_drift.csv")

    _render_overview(screenshots_dir / "overview.png", overview_rows, health_rows)
    _render_table(
        screenshots_dir / "dtc_correlation.png",
        "DTC correlation",
        dtc_rows[:8],
        ["session_id", "code", "status", "fault_ts", "rpm", "engine_load_pct", "coolant_temp_c"],
    )
    _render_table(
        screenshots_dir / "fuel_trim_drift.png",
        "Fuel trim drift",
        drift_rows[:10],
        ["session_id", "ts", "ltft_b1_pct", "ltft_30s"],
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _render_overview(path: Path, overview_rows: list[dict[str, str]], health_rows: list[dict[str, str]]) -> None:
    image = _canvas()
    draw = ImageDraw.Draw(image)
    font_title = _font(42)
    font_label = _font(22)
    font_small = _font(18)

    draw.text((56, 48), "Corvus Power BI v1", fill=OFF_WHITE, font=font_title)
    draw.text((58, 104), "SQLite-backed OBD-II report pack", fill="#cbbca9", font=font_small)

    health_by_session = {row["session_id"]: row for row in health_rows}
    x = 58
    for row in overview_rows:
        health = health_by_session.get(row["session_id"], {})
        _card(draw, x, 166, 292, 168)
        draw.text((x + 22, 188), f"Session {row['session_id']}", fill=UHCHI_TEAL, font=font_label)
        draw.text((x + 22, 228), f"{row['make']} {row['model']}", fill=OFF_WHITE, font=font_label)
        draw.text((x + 22, 266), f"Health {health.get('health_score', 'n/a')}", fill=UHCHI_RED, font=font_label)
        draw.text((x + 22, 302), f"Rows {row['telemetry_samples']}", fill="#cbbca9", font=font_small)
        x += 326

    draw.text((58, 402), "Pages", fill=OFF_WHITE, font=font_label)
    for index, label in enumerate(("Drive health", "Fuel trim", "DTC evidence")):
        y = 452 + index * 52
        draw.rounded_rectangle((58, y, 520, y + 34), radius=10, outline=UHCHI_TEAL, width=2)
        draw.text((78, y + 5), label, fill=OFF_WHITE, font=font_small)

    image.save(path)


def _render_table(path: Path, title: str, rows: list[dict[str, str]], columns: list[str]) -> None:
    image = _canvas()
    draw = ImageDraw.Draw(image)
    font_title = _font(42)
    font_head = _font(17)
    font_cell = _font(15)

    draw.text((56, 48), title, fill=OFF_WHITE, font=font_title)
    draw.text((58, 104), "Values are exported from SQL output", fill="#cbbca9", font=font_cell)

    x0, y0 = 56, 166
    widths = [118, 190, 110, 222, 100, 148, 148][: len(columns)]
    x = x0
    for column, width in zip(columns, widths, strict=True):
        draw.text((x + 10, y0 + 12), column, fill=UHCHI_TEAL, font=font_head)
        x += width
    draw.line((x0, y0 + 42, 1168, y0 + 42), fill=UHCHI_TEAL, width=2)

    for row_index, row in enumerate(rows):
        y = y0 + 58 + row_index * 42
        x = x0
        for column, width in zip(columns, widths, strict=True):
            value = str(row.get(column, ""))[:22]
            draw.text((x + 10, y), value, fill=OFF_WHITE, font=font_cell)
            x += width
        draw.line((x0, y + 30, 1168, y + 30), fill="#3a3a3a", width=1)

    image.save(path)


def _canvas() -> Image.Image:
    return Image.new("RGB", (1240, 720), UHCHI_DARK)


def _card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    draw.rounded_rectangle((x + 8, y + 8, x + w + 8, y + h + 8), radius=12, fill=UHCHI_TEAL)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=PANEL, outline="#4b4b4b", width=1)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "segoeuib.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
