from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.ingest.csv_adapter import ingest_drive_csv  # noqa: E402
from src.ingest.database import (  # noqa: E402
    SessionMetadata,
    VehicleMetadata,
    connect_sqlite,
    initialize_database,
    insert_demo_baselines,
)
from src.ingest.emulator_adapter import ingest_emulator_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Corvus SQLite demo database.")
    parser.add_argument("--database", default=str(ROOT / "data" / "seed" / "corvus.db"))
    args = parser.parse_args()

    db_path = Path(args.database)
    initialize_database(db_path, ROOT / "data" / "schema.sql")

    vehicle = VehicleMetadata(
        vin="DEMO-CORVUS-LS1",
        make="Chevrolet",
        model="Corvette",
        year=2002,
        engine="LS1 5.7L V8",
        notes="Synthetic demo vehicle; not a real VIN.",
    )

    with connect_sqlite(db_path) as conn:
        csv_result = ingest_drive_csv(
            conn,
            ROOT / "data" / "seed" / "sample_ls1_drive.csv",
            vehicle,
            SessionMetadata(
                source="csv",
                ambient_c=21.0,
                notes="Synthetic Torque/Car Scanner style CSV for offline development.",
            ),
        )
        insert_demo_baselines(conn, csv_result.vehicle_id)

        emulator_result = ingest_emulator_csv(
            conn,
            ROOT / "data" / "seed" / "emulator_ls1_drive.csv",
            vehicle,
            notes="Synthetic ELM327-emulator scenario exported as CSV.",
        )
        insert_demo_baselines(conn, emulator_result.vehicle_id)

        public_vehicle = VehicleMetadata(
            vin=None,
            make="Seat",
            model="Leon",
            year=None,
            engine=None,
            notes="Public KIT Automotive OBD-II Dataset sample; DOI 10.35097/1130.",
        )
        public_result = ingest_drive_csv(
            conn,
            ROOT / "data" / "seed" / "public_obd_kit_sample.csv",
            public_vehicle,
            SessionMetadata(
                source="csv",
                notes="Normalized public OBD-II CSV slice from KIT/RADAR under CC BY 4.0.",
            ),
        )
        insert_demo_baselines(conn, public_result.vehicle_id)
        conn.commit()

    print(f"Seeded {db_path}")
    print(
        "Rows: "
        f"csv telemetry={csv_result.telemetry_rows}, csv dtcs={csv_result.dtc_rows}; "
        f"emulator telemetry={emulator_result.telemetry_rows}, emulator dtcs={emulator_result.dtc_rows}; "
        f"public telemetry={public_result.telemetry_rows}, public dtcs={public_result.dtc_rows}"
    )


if __name__ == "__main__":
    main()
