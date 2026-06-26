from __future__ import annotations

import argparse
import csv
import hashlib
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_URL = "https://www.radar-service.eu/radar-backend/archives/bCtGxdTklQlfQcAq/versions/1/content"
ARCHIVE_MD5 = "22d9aac00d1a2b4c97aa35fd7a103ba4"
SOURCE_FILE = "2018-03-29_Seat_Leon_KA_RT_Stau.csv"
PUBLIC_SEED_SOURCES = {
    "public_obd_kit_normal.csv": "2018-03-21_Seat_Leon_KA_RT_Normal.csv",
}

SOURCE_COLUMNS = {
    "rpm": "Engine RPM [RPM]",
    "speed_kph": "Vehicle Speed Sensor [km/h]",
    "coolant_temp_c": "Engine Coolant Temperature [°C]",
    "intake_temp_c": "Intake Air Temperature [°C]",
    "maf_gps": "Air Flow Rate from Mass Flow Sensor [g/s]",
    "throttle_pct": "Absolute Throttle Position [%]",
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
        description="Fetch KIT's public OBD-II dataset and write a Corvus seed CSV slice."
    )
    parser.add_argument("--work-dir", default=str(ROOT / "work" / "public-obd"))
    parser.add_argument("--output", default=str(ROOT / "data" / "seed" / "public_obd_kit_sample.csv"))
    parser.add_argument("--source-file", default=SOURCE_FILE)
    parser.add_argument("--max-rows", type=int, default=240)
    parser.add_argument("--all-dashboard-seeds", action="store_true")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    output_path = Path(args.output)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    archive_path = work_dir / "kit_obd_dataset.tar"
    if not archive_path.exists():
        urllib.request.urlretrieve(DATASET_URL, archive_path)
    _verify_md5(archive_path)

    if args.all_dashboard_seeds:
        for filename, source_file in PUBLIC_SEED_SOURCES.items():
            csv_path = _extract_source_csv(archive_path, work_dir, source_file)
            seed_path = output_path.parent / filename
            _write_normalized_seed(csv_path, seed_path, args.max_rows)
        return

    csv_path = _extract_source_csv(archive_path, work_dir, args.source_file)
    _write_normalized_seed(csv_path, output_path, args.max_rows)


def _verify_md5(path: Path) -> None:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != ARCHIVE_MD5:
        raise SystemExit(f"Unexpected archive checksum for {path}")


def _extract_source_csv(archive_path: Path, work_dir: Path, source_file: str) -> Path:
    extracted_dir = work_dir / "extracted"
    unzipped_dir = work_dir / "unzipped"
    csv_path = unzipped_dir / "OBD-II-Dataset" / source_file
    if csv_path.exists():
        return csv_path

    extracted_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path) as archive:
        archive.extractall(extracted_dir)

    dataset_zip = extracted_dir / "10.35097-1130" / "data" / "dataset" / "OBD-II-Dataset.zip"
    if not dataset_zip.exists():
        raise FileNotFoundError(f"Dataset zip not found: {dataset_zip}")

    unzipped_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dataset_zip) as archive:
        archive.extractall(unzipped_dir)

    if not csv_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")
    return csv_path


def _write_normalized_seed(csv_path: Path, output_path: Path, max_rows: int) -> None:
    rows = _normalized_rows(csv_path, max_rows)
    if not rows:
        raise SystemExit(f"No normalized rows written from {csv_path}")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows from {csv_path.name} to {output_path}")


def _normalized_rows(csv_path: Path, max_rows: int) -> list[dict[str, str]]:
    date_prefix = csv_path.name.split("_", 1)[0]
    last_values = dict.fromkeys(SOURCE_COLUMNS, "")
    rows: list[dict[str, str]] = []
    emitted_seconds: set[str] = set()

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for output_column, source_column in SOURCE_COLUMNS.items():
                value = (row.get(source_column) or "").strip()
                if value:
                    last_values[output_column] = value

            if not all(last_values.values()):
                continue

            timestamp = _timestamp(date_prefix, row["Time"])
            second_key = timestamp[:19]
            if second_key in emitted_seconds:
                continue
            emitted_seconds.add(second_key)

            output_row = {column: "" for column in OUTPUT_COLUMNS}
            output_row.update(last_values)
            output_row["ts"] = timestamp
            rows.append(output_row)

            if len(rows) >= max_rows:
                break

    return rows


def _timestamp(date_prefix: str, time_value: str) -> str:
    return f"{date_prefix}T{time_value.strip()}Z"


if __name__ == "__main__":
    main()
