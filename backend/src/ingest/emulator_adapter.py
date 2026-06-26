from __future__ import annotations

import sqlite3
from pathlib import Path

from .csv_adapter import ingest_drive_csv
from .database import IngestResult, SessionMetadata, VehicleMetadata


def ingest_emulator_csv(
    conn: sqlite3.Connection,
    csv_path: str | Path,
    vehicle: VehicleMetadata,
    notes: str | None = None,
) -> IngestResult:
    session = SessionMetadata(
        source="emulator",
        ambient_c=22.0,
        notes=notes or "Synthetic no-hardware ELM327-emulator scenario CSV.",
    )
    return ingest_drive_csv(conn, csv_path, vehicle, session)

