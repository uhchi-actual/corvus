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
    insert_reference_baselines,
)
from src.ingest.emulator_adapter import ingest_emulator_csv  # noqa: E402

PUBLIC_DRIVE_SOURCES = [
    {
        "seed_file": "public_obd_kit_normal.csv",
        "source_file": "2018-03-26_Seat_Leon_S_RT_Stau.csv",
        "label": "Traffic Jam Log",
        "vehicle": VehicleMetadata(
            vin=None,
            make="Seat",
            model="Leon",
            year=None,
            engine=None,
            notes="Public KIT Automotive OBD-II Dataset sample; DOI 10.35097/1130.",
        ),
        "dataset": "KIT/RADAR Automotive OBD-II Dataset",
        "license": "CC BY 4.0",
    },
    {
        "seed_file": "public_obd_caro_etios_1p5l.csv",
        "source_file": "carOBD live1.csv (Toyota Etios 2014)",
        "label": "City Commute Log",
        "vehicle": VehicleMetadata(
            vin=None,
            make="Toyota",
            model="Etios 1.5L",
            year=2014,
            engine="4-FI 1.5L",
            notes="Public carOBD dataset (eron93br/carOBD); 1496cc; free with citation.",
        ),
        "dataset": "carOBD (Toyota Etios)",
        "license": "Open / cite author",
    },
    {
        "seed_file": "public_obd_opel_corsa_1p2l.csv",
        "source_file": "dataset.csv (Opel Corsa 2012)",
        "label": "Mixed Roads Log",
        "vehicle": VehicleMetadata(
            vin=None,
            make="Opel",
            model="Corsa 1.2L",
            year=2012,
            engine="4-FI 1.2L",
            notes="Public OBD2 panel Opel 2012 dataset (Kaggle pedro2025); A12XER 1.2L.",
        ),
        "dataset": "OBD2 panel Opel 2012",
        "license": "see Kaggle data card",
    },
]


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
        notes="Synthetic control vehicle for agent pipeline testing; not a real VIN.",
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
        insert_demo_baselines(conn, csv_result.vehicle_id, vehicle.engine)

        emulator_result = ingest_emulator_csv(
            conn,
            ROOT / "data" / "seed" / "emulator_ls1_drive.csv",
            vehicle,
            notes="Synthetic ELM327-emulator scenario exported as CSV.",
        )
        insert_demo_baselines(conn, emulator_result.vehicle_id, vehicle.engine)

        public_results = []
        for source in PUBLIC_DRIVE_SOURCES:
            trip_ref = source.get("source_detail", "")
            trip_suffix = f"trip_ref={trip_ref}; " if trip_ref else ""
            public_result = ingest_drive_csv(
                conn,
                ROOT / "data" / "seed" / source["seed_file"],
                source["vehicle"],
                SessionMetadata(
                    source="public",
                    notes=(
                        f"{source['dataset']} real OBD-II entry; "
                        f"source_file={source['source_file']}; "
                        f"{trip_suffix}"
                        f"drive_label={source['label']}; "
                        f"license={source['license']}."
                    ),
                ),
            )
            insert_reference_baselines(conn, public_result.vehicle_id, source["vehicle"].engine)
            public_results.append(public_result)
        conn.commit()

    print(f"Seeded {db_path}")
    public_telemetry_rows = sum(result.telemetry_rows for result in public_results)
    public_dtc_rows = sum(result.dtc_rows for result in public_results)
    print(
        "Rows: "
        f"csv telemetry={csv_result.telemetry_rows}, csv dtcs={csv_result.dtc_rows}; "
        f"emulator telemetry={emulator_result.telemetry_rows}, emulator dtcs={emulator_result.dtc_rows}; "
        f"public telemetry={public_telemetry_rows}, public dtc_rows={public_dtc_rows}"
    )


if __name__ == "__main__":
    main()
