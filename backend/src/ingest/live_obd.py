from __future__ import annotations

import importlib
import sqlite3
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from .database import IngestResult, SessionMetadata, VehicleMetadata, insert_session, insert_vehicle

READ_ONLY_COMMAND_NAMES = {
    "RPM": "rpm",
    "SPEED": "speed_kph",
    "ENGINE_LOAD": "engine_load_pct",
    "COOLANT_TEMP": "coolant_temp_c",
    "INTAKE_TEMP": "intake_temp_c",
    "MAF": "maf_gps",
    "THROTTLE_POS": "throttle_pct",
    "SHORT_FUEL_TRIM_1": "stft_b1_pct",
    "LONG_FUEL_TRIM_1": "ltft_b1_pct",
    "TIMING_ADVANCE": "timing_adv_deg",
    "FUEL_PRESSURE": "fuel_press_kpa",
    "O2_B1S1": "o2_b1s1_v",
}
READ_ONLY_DTC_COMMANDS = ("GET_DTC", "GET_CURRENT_DTC")
READ_ONLY_IDENTITY_COMMANDS = ("VIN",)
FORBIDDEN_COMMAND_NAMES = {"CLEAR_DTC"}


def capture_live_session(
    conn: sqlite3.Connection,
    vehicle: VehicleMetadata,
    sample_count: int,
    sample_interval_seconds: float = 1.0,
    port: str = "auto",
    obd_module: Any | None = None,
    now: Callable[[], datetime] | None = None,
) -> IngestResult:
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")

    obd = obd_module or importlib.import_module("obd")
    commands = obd.commands
    _assert_read_only_commands(commands)

    connection = obd.OBD() if port == "auto" else obd.OBD(port)
    clock = now or (lambda: datetime.now(UTC))
    vin = _query_text(connection, getattr(commands, "VIN", None)) or vehicle.vin

    vehicle_id = insert_vehicle(conn, replace(vehicle, vin=vin))
    session = SessionMetadata(source="live", notes=f"Live python-OBD capture from port={port}.")
    started_at = clock().isoformat()
    session_id = insert_session(conn, vehicle_id, session, started_at, started_at)

    telemetry_rows = 0
    for index in range(sample_count):
        ts = clock().isoformat()
        sample = {
            column: _query_number(connection, getattr(commands, command_name, None))
            for command_name, column in READ_ONLY_COMMAND_NAMES.items()
        }
        conn.execute(
            """
            INSERT INTO telemetry_samples
              (session_id, ts, rpm, speed_kph, engine_load_pct, coolant_temp_c,
               intake_temp_c, maf_gps, throttle_pct, stft_b1_pct, ltft_b1_pct,
               timing_adv_deg, fuel_press_kpa, o2_b1s1_v)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                ts,
                sample["rpm"],
                sample["speed_kph"],
                sample["engine_load_pct"],
                sample["coolant_temp_c"],
                sample["intake_temp_c"],
                sample["maf_gps"],
                sample["throttle_pct"],
                sample["stft_b1_pct"],
                sample["ltft_b1_pct"],
                sample["timing_adv_deg"],
                sample["fuel_press_kpa"],
                sample["o2_b1s1_v"],
            ),
        )
        telemetry_rows += 1
        if index < sample_count - 1:
            time.sleep(sample_interval_seconds)

    dtc_rows = _insert_live_dtcs(conn, connection, commands, session_id, clock().isoformat())
    ended_at = clock().isoformat()
    conn.execute(
        "UPDATE drive_sessions SET ended_at = ? WHERE session_id = ?",
        (ended_at, session_id),
    )
    conn.commit()
    return IngestResult(vehicle_id, session_id, telemetry_rows, dtc_rows)


def _insert_live_dtcs(
    conn: sqlite3.Connection,
    connection: Any,
    commands: Any,
    session_id: int,
    ts: str,
) -> int:
    dtc_rows = 0
    for command_name, status in (("GET_DTC", "stored"), ("GET_CURRENT_DTC", "pending")):
        for code, description in _query_dtcs(connection, getattr(commands, command_name, None)):
            conn.execute(
                """
                INSERT INTO dtc_events (session_id, ts, code, status, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, ts, code, status, description),
            )
            dtc_rows += 1
    return dtc_rows


def _assert_read_only_commands(commands: Any) -> None:
    for command_name in (
        *READ_ONLY_COMMAND_NAMES.keys(),
        *READ_ONLY_DTC_COMMANDS,
        *READ_ONLY_IDENTITY_COMMANDS,
    ):
        if not hasattr(commands, command_name):
            raise AttributeError(f"python-OBD command is missing: {command_name}")


def _query_number(connection: Any, command: Any) -> float | None:
    if command is None:
        return None
    response = connection.query(command)
    if _is_null_response(response):
        return None
    return _number_from_value(response.value)


def _query_text(connection: Any, command: Any) -> str | None:
    if command is None:
        return None
    response = connection.query(command)
    if _is_null_response(response):
        return None
    value = response.value
    if value is None:
        return None
    return str(value).strip() or None


def _query_dtcs(connection: Any, command: Any) -> list[tuple[str, str | None]]:
    if command is None:
        return []
    response = connection.query(command)
    if _is_null_response(response) or response.value is None:
        return []
    return [(str(code), description) for code, description in response.value]


def _is_null_response(response: Any) -> bool:
    return response is None or bool(getattr(response, "is_null", lambda: False)())


def _number_from_value(value: Any) -> float | None:
    if value is None:
        return None
    magnitude = getattr(value, "magnitude", value)
    try:
        return float(magnitude)
    except (TypeError, ValueError):
        return None
