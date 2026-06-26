from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "seed" / "corvus.db"
EXPECTED_TABLES = {
    "vehicles",
    "drive_sessions",
    "telemetry_samples",
    "dtc_events",
    "baselines",
    "findings",
}


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(DB_PATH)],
        check=True,
    )

    with sqlite3.connect(DB_PATH) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        missing_tables = EXPECTED_TABLES - tables
        if missing_tables:
            raise SystemExit(f"Missing schema tables: {sorted(missing_tables)}")

        session_sources = {
            row[0] for row in conn.execute("SELECT DISTINCT source FROM drive_sessions")
        }
        if session_sources != {"csv", "emulator"}:
            raise SystemExit(f"Unexpected session sources: {sorted(session_sources)}")

        telemetry_count = conn.execute("SELECT COUNT(*) FROM telemetry_samples").fetchone()[0]
        dtc_count = conn.execute("SELECT COUNT(*) FROM dtc_events").fetchone()[0]
        baseline_count = conn.execute("SELECT COUNT(*) FROM baselines").fetchone()[0]
        if telemetry_count != 24 or dtc_count != 2 or baseline_count != 10:
            raise SystemExit(
                "Unexpected seed counts: "
                f"telemetry={telemetry_count}, dtc={dtc_count}, baselines={baseline_count}"
            )

    live_adapter = (ROOT / "backend" / "src" / "ingest" / "live_obd.py").read_text(
        encoding="utf-8"
    )
    if "CLEAR_DTC" not in live_adapter or "connection.query(commands.CLEAR_DTC)" in live_adapter:
        raise SystemExit("Live adapter Mode 04 guardrail is missing or violated")

    verification = (ROOT / "docs" / "OBD_VERIFICATION.md").read_text(encoding="utf-8")
    if "a378bdd81d58c67d08050e4244173a9a7dbda73d" not in verification:
        raise SystemExit("OBD verification source commit is not documented")

    print("Phase 1 ingest contract OK")


if __name__ == "__main__":
    main()

