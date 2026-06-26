from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VED_REPO = "https://github.com/gsoh/VED.git"
VED_WEEK_ARCHIVE = "Data/VED_DynamicData_Part1.7z"
VED_WEEK_FILE = "VED_171101_week.csv"
VED_REFERENCE = datetime(2017, 11, 1)

VED_DASHBOARD_SLICES = {
    "public_obd_ved_6l_v8.csv": {
        "veh_id": "108",
        "trip": "784",
        "drive_label": "Ann Arbor week log",
    },
    "public_obd_ved_car_1p5l.csv": {
        "veh_id": "8",
        "trip": "708",
        "drive_label": "Ann Arbor week log",
    },
}

OUTPUT_COLUMNS = [
    "ts",
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
    "dtc_code",
    "dtc_status",
    "dtc_description",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch VED public OBD-II slices and write Corvus seed CSV files."
    )
    parser.add_argument("--work-dir", default=str(ROOT / "work" / "ved"))
    parser.add_argument("--max-rows", type=int, default=240)
    parser.add_argument("--all-dashboard-seeds", action="store_true")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    week_csv = _ensure_week_csv(work_dir)
    seed_dir = ROOT / "data" / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)

    if args.all_dashboard_seeds:
        for filename, selection in VED_DASHBOARD_SLICES.items():
            _write_slice(
                week_csv,
                seed_dir / filename,
                selection["veh_id"],
                selection["trip"],
                args.max_rows,
            )
        return

    raise SystemExit("Pass --all-dashboard-seeds to write tracked VED dashboard slices.")


def _ensure_week_csv(work_dir: Path) -> Path:
    week_csv = work_dir / "extracted" / VED_WEEK_FILE
    if week_csv.exists():
        return week_csv

    repo_dir = work_dir / "repo"
    if not (repo_dir / ".git").exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", VED_REPO, str(repo_dir)],
            check=True,
        )

    archive_path = repo_dir / VED_WEEK_ARCHIVE
    if not archive_path.exists():
        raise FileNotFoundError(f"VED archive not found: {archive_path}")

    week_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        import py7zr
    except ImportError:
        raise SystemExit("py7zr is required. Install with: pip install py7zr")

    with py7zr.SevenZipFile(archive_path, "r") as archive:
        archive.extract(targets=[VED_WEEK_FILE], path=week_csv.parent)
    if not week_csv.exists():
        raise FileNotFoundError(f"VED week file missing after extract: {week_csv}")
    return week_csv


def _write_slice(
    week_csv: Path,
    output_path: Path,
    veh_id: str,
    trip: str,
    max_rows: int,
) -> None:
    rows = _normalized_rows(week_csv, veh_id, trip, max_rows)
    if not rows:
        raise SystemExit(f"No normalized VED rows for VehId={veh_id} Trip={trip}")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Wrote {len(rows)} rows from {week_csv.name} "
        f"(VehId={veh_id}, Trip={trip}) to {output_path}"
    )


def _normalized_rows(
    week_csv: Path,
    veh_id: str,
    trip: str,
    max_rows: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with week_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["VehId"] != veh_id or row["Trip"] != trip:
                continue

            rpm = _float_text(row.get("Engine RPM[RPM]"))
            speed = _float_text(row.get("Vehicle Speed[km/h]"))
            load = _float_text(row.get("Absolute Load[%]"))
            maf = _float_text(row.get("MAF[g/sec]"))
            if not all([rpm, speed, load, maf]):
                continue

            output_row = {column: "" for column in OUTPUT_COLUMNS}
            output_row["ts"] = _timestamp(row["DayNum"], row["Timestamp(ms)"])
            output_row["rpm"] = rpm
            output_row["speed_kph"] = speed
            output_row["engine_load_pct"] = load
            output_row["maf_gps"] = maf
            output_row["stft_b1_pct"] = _float_text(row.get("Short Term Fuel Trim Bank 1[%]"))
            output_row["ltft_b1_pct"] = _float_text(row.get("Long Term Fuel Trim Bank 1[%]"))
            rows.append(output_row)

            if len(rows) >= max_rows:
                break

    return rows


def _timestamp(day_num: str, timestamp_ms: str) -> str:
    day_offset = float(day_num) - 1.0
    milliseconds = int(float(timestamp_ms))
    ts = VED_REFERENCE + timedelta(days=day_offset, milliseconds=milliseconds)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"


def _float_text(value: str | None) -> str:
    if value is None:
        return ""
    stripped = value.strip()
    if not stripped or stripped.upper() == "NA":
        return ""
    return stripped


if __name__ == "__main__":
    main()
