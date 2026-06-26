from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from src.ingest.csv_adapter import ingest_drive_csv
from src.ingest.database import SessionMetadata, VehicleMetadata, initialize_database
from src.ingest.emulator_adapter import ingest_emulator_csv
from src.ingest.live_obd import FORBIDDEN_COMMAND_NAMES, capture_live_session

ROOT = Path(__file__).resolve().parents[2]


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _new_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "corvus.db"
    initialize_database(db_path, ROOT / "data" / "schema.sql")
    return db_path


def test_csv_ingest_loads_telemetry_and_dtc(tmp_path: Path) -> None:
    db_path = _new_db(tmp_path)
    with _connect(db_path) as conn:
        result = ingest_drive_csv(
            conn,
            ROOT / "data" / "seed" / "sample_ls1_drive.csv",
            VehicleMetadata(vin="DEMO", make="Chevrolet", model="Corvette"),
            SessionMetadata(source="csv", ambient_c=21.0, notes="test"),
        )

        assert result.telemetry_rows == 12
        assert result.dtc_rows == 1
        assert conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM drive_sessions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM telemetry_samples").fetchone()[0] == 12

        dtc = conn.execute("SELECT code, status FROM dtc_events").fetchone()
        assert dict(dtc) == {"code": "P0171", "status": "pending"}


def test_emulator_ingest_marks_session_source(tmp_path: Path) -> None:
    db_path = _new_db(tmp_path)
    with _connect(db_path) as conn:
        result = ingest_emulator_csv(
            conn,
            ROOT / "data" / "seed" / "emulator_ls1_drive.csv",
            VehicleMetadata(vin="EMU", make="Chevrolet", model="Corvette"),
        )

        assert result.telemetry_rows == 12
        source = conn.execute("SELECT source FROM drive_sessions").fetchone()[0]
        assert source == "emulator"


def test_live_obd_adapter_uses_verified_read_only_commands(tmp_path: Path) -> None:
    db_path = _new_db(tmp_path)
    fake_obd = FakeObdModule()
    clock = FakeClock(datetime(2026, 6, 3, 12, 0, tzinfo=UTC))

    with _connect(db_path) as conn:
        result = capture_live_session(
            conn,
            VehicleMetadata(make="Chevrolet", model="Corvette"),
            sample_count=2,
            sample_interval_seconds=0,
            obd_module=fake_obd,
            now=clock,
        )

        assert result.telemetry_rows == 2
        assert result.dtc_rows == 2
        assert conn.execute("SELECT vin FROM vehicles").fetchone()[0] == "TESTVIN1234567890"
        assert conn.execute("SELECT COUNT(*) FROM telemetry_samples").fetchone()[0] == 2

    queried = set(fake_obd.connection.queried)
    assert "CLEAR_DTC" not in queried
    assert queried.isdisjoint(FORBIDDEN_COMMAND_NAMES)
    assert {"GET_DTC", "GET_CURRENT_DTC", "VIN"}.issubset(queried)


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def __call__(self) -> datetime:
        value = self.current
        self.current += timedelta(seconds=1)
        return value


class FakeValue:
    def __init__(self, magnitude: float) -> None:
        self.magnitude = magnitude


class FakeResponse:
    def __init__(self, value: object) -> None:
        self.value = value

    def is_null(self) -> bool:
        return False


class FakeConnection:
    def __init__(self) -> None:
        self.queried: list[str] = []

    def query(self, command: object) -> FakeResponse:
        name = str(command)
        self.queried.append(name)
        if name == "VIN":
            return FakeResponse("TESTVIN1234567890")
        if name == "GET_DTC":
            return FakeResponse([("P0171", "System Too Lean Bank 1")])
        if name == "GET_CURRENT_DTC":
            return FakeResponse([("P0301", "Cylinder 1 Misfire Detected")])
        return FakeResponse(FakeValue(42.0))


class FakeObdModule:
    def __init__(self) -> None:
        names = [
            "RPM",
            "SPEED",
            "ENGINE_LOAD",
            "COOLANT_TEMP",
            "INTAKE_TEMP",
            "MAF",
            "THROTTLE_POS",
            "SHORT_FUEL_TRIM_1",
            "LONG_FUEL_TRIM_1",
            "TIMING_ADVANCE",
            "FUEL_PRESSURE",
            "O2_B1S1",
            "GET_DTC",
            "GET_CURRENT_DTC",
            "VIN",
            "CLEAR_DTC",
        ]
        self.commands = SimpleNamespace(**{name: name for name in names})
        self.connection = FakeConnection()

    def OBD(self, *_args: object, **_kwargs: object) -> FakeConnection:
        return self.connection
