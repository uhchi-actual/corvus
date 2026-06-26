from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VehicleMetadata:
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    engine: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class SessionMetadata:
    source: str
    ambient_c: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class IngestResult:
    vehicle_id: int
    session_id: int
    telemetry_rows: int
    dtc_rows: int


def connect_sqlite(database_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(database_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_schema(conn: sqlite3.Connection, schema_path: str | Path) -> None:
    conn.executescript(Path(schema_path).read_text(encoding="utf-8"))
    conn.commit()


def initialize_database(database_path: str | Path, schema_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    with connect_sqlite(path) as conn:
        load_schema(conn, schema_path)


def insert_vehicle(conn: sqlite3.Connection, vehicle: VehicleMetadata) -> int:
    cur = conn.execute(
        """
        INSERT INTO vehicles (vin, make, model, year, engine, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (vehicle.vin, vehicle.make, vehicle.model, vehicle.year, vehicle.engine, vehicle.notes),
    )
    return int(cur.lastrowid)


def insert_session(
    conn: sqlite3.Connection,
    vehicle_id: int,
    session: SessionMetadata,
    started_at: str,
    ended_at: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO drive_sessions
          (vehicle_id, started_at, ended_at, source, ambient_c, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (vehicle_id, started_at, ended_at, session.source, session.ambient_c, session.notes),
    )
    return int(cur.lastrowid)


def insert_demo_baselines(conn: sqlite3.Connection, vehicle_id: int) -> None:
    rows = [
        ("coolant_temp_c", "warm", 82.0, 105.0, "C", "manual"),
        ("ltft_b1_pct", "cruise", -10.0, 10.0, "%", "manual"),
        ("stft_b1_pct", "cruise", -10.0, 10.0, "%", "manual"),
        ("engine_load_pct", "idle", 12.0, 35.0, "%", "manual"),
        ("timing_adv_deg", "cruise", 10.0, 45.0, "deg", "manual"),
    ]
    conn.executemany(
        """
        INSERT INTO baselines
          (vehicle_id, metric, context, healthy_min, healthy_max, unit, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [(vehicle_id, *row) for row in rows],
    )

