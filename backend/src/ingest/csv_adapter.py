from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

from .database import IngestResult, SessionMetadata, VehicleMetadata, insert_session, insert_vehicle

TELEMETRY_COLUMNS = (
    "rpm",
    "speed_kph",
    "engine_load_pct",
    "coolant_temp_c",
    "intake_temp_c",
    "maf_gps",
    "throttle_pct",
    "stft_b1_pct",
    "ltft_b1_pct",
    "timing_adv_deg",
    "fuel_press_kpa",
    "o2_b1s1_v",
)

COLUMN_ALIASES = {
    "ts": ("ts", "timestamp", "time", "datetime"),
    "rpm": ("rpm", "engine rpm", "engine rpm(rpm)", "engine rpm (rpm)", "engine rpm[rpm]"),
    "speed_kph": (
        "speed_kph",
        "speed",
        "speed (km/h)",
        "vehicle speed(km/h)",
        "vehicle speed[km/h]",
    ),
    "engine_load_pct": (
        "engine_load_pct",
        "engine load",
        "engine load(%)",
        "engine load (%)",
        "absolute load[%]",
    ),
    "coolant_temp_c": (
        "coolant_temp_c",
        "coolant temp",
        "coolant temp(c)",
        "engine coolant temperature(c)",
    ),
    "intake_temp_c": ("intake_temp_c", "intake temp", "intake air temp(c)"),
    "maf_gps": ("maf_gps", "maf", "maf(g/s)", "mass air flow(g/s)", "maf[g/sec]"),
    "throttle_pct": ("throttle_pct", "throttle position(%)", "throttle position"),
    "stft_b1_pct": (
        "stft_b1_pct",
        "short fuel trim bank 1(%)",
        "short fuel trim 1",
        "short term fuel trim bank 1[%]",
    ),
    "ltft_b1_pct": (
        "ltft_b1_pct",
        "long fuel trim bank 1(%)",
        "long fuel trim 1",
        "long term fuel trim bank 1[%]",
    ),
    "timing_adv_deg": ("timing_adv_deg", "timing advance", "timing advance(deg)"),
    "fuel_press_kpa": ("fuel_press_kpa", "fuel pressure(kpa)", "fuel pressure"),
    "o2_b1s1_v": ("o2_b1s1_v", "o2 b1s1(v)", "o2_b1s1", "bank 1 sensor 1 voltage(v)"),
    "dtc_code": ("dtc_code", "dtc", "code", "trouble code"),
    "dtc_status": ("dtc_status", "status", "dtc status"),
    "dtc_description": ("dtc_description", "description", "dtc description"),
}

FLOAT_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def ingest_drive_csv(
    conn: sqlite3.Connection,
    csv_path: str | Path,
    vehicle: VehicleMetadata,
    session: SessionMetadata,
) -> IngestResult:
    rows = list(_read_rows(csv_path))
    if not rows:
        raise ValueError(f"No telemetry rows found in {csv_path}")

    vehicle_id = insert_vehicle(conn, vehicle)
    started_at = rows[0]["ts"]
    ended_at = rows[-1]["ts"]
    session_id = insert_session(conn, vehicle_id, session, started_at, ended_at)

    telemetry_payload = [
        (session_id, row["ts"], *[row[column] for column in TELEMETRY_COLUMNS]) for row in rows
    ]
    conn.executemany(
        """
        INSERT INTO telemetry_samples
          (session_id, ts, rpm, speed_kph, engine_load_pct, coolant_temp_c,
           intake_temp_c, maf_gps, throttle_pct, stft_b1_pct, ltft_b1_pct,
           timing_adv_deg, fuel_press_kpa, o2_b1s1_v)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        telemetry_payload,
    )

    dtc_payload = []
    seen_dtc_keys = set()
    for row in rows:
        for code in _split_codes(row.get("dtc_code")):
            key = (row["ts"], code, row.get("dtc_status") or "stored")
            if key in seen_dtc_keys:
                continue
            seen_dtc_keys.add(key)
            dtc_payload.append(
                (
                    session_id,
                    row["ts"],
                    code,
                    row.get("dtc_status") or "stored",
                    row.get("dtc_description"),
                )
            )

    if dtc_payload:
        conn.executemany(
            """
            INSERT INTO dtc_events (session_id, ts, code, status, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            dtc_payload,
        )

    conn.commit()
    return IngestResult(vehicle_id, session_id, len(telemetry_payload), len(dtc_payload))


def _read_rows(csv_path: str | Path) -> list[dict[str, float | str | None]]:
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        field_lookup = _field_lookup(reader.fieldnames)
        return [_normalize_row(row, field_lookup) for row in reader]


def _field_lookup(fieldnames: list[str]) -> dict[str, str]:
    normalized = {_normalize_header(name): name for name in fieldnames}
    lookup = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            source = normalized.get(_normalize_header(alias))
            if source is not None:
                lookup[canonical] = source
                break
    if "ts" not in lookup:
        raise ValueError("CSV is missing a timestamp column")
    return lookup


def _normalize_row(
    row: dict[str, str],
    field_lookup: dict[str, str],
) -> dict[str, float | str | None]:
    normalized: dict[str, float | str | None] = {"ts": _required_text(row, field_lookup, "ts")}
    for column in TELEMETRY_COLUMNS:
        normalized[column] = _float_or_none(row.get(field_lookup.get(column, "")))
    for column in ("dtc_code", "dtc_status", "dtc_description"):
        normalized[column] = _text_or_none(row.get(field_lookup.get(column, "")))
    return normalized


def _required_text(row: dict[str, str], field_lookup: dict[str, str], column: str) -> str:
    value = _text_or_none(row.get(field_lookup[column]))
    if value is None:
        raise ValueError(f"CSV row is missing required value: {column}")
    return value


def _text_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    match = FLOAT_RE.search(value.replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def _split_codes(value: float | str | None) -> list[str]:
    if value is None or isinstance(value, float):
        return []
    return [code.strip().upper() for code in re.split(r"[;|,]", value) if code.strip()]


def _normalize_header(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())
