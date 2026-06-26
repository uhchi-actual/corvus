from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "powerbi" / "export"
SCREENSHOT_DIR = ROOT / "powerbi" / "screenshots"

EXPECTED_EXPORTS = {
    "vehicles.csv",
    "drive_sessions.csv",
    "telemetry_samples.csv",
    "dtc_events.csv",
    "baselines.csv",
    "session_overview.csv",
    "health_scores.csv",
    "baseline_deviation.csv",
    "fuel_trim_drift.csv",
    "dtc_telemetry_correlation.csv",
    "findings.csv",
}

EXPECTED_SCREENSHOTS = {
    "overview.png",
    "dtc_correlation.png",
    "fuel_trim_drift.png",
}


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_powerbi_dataset.py"), "--refresh-db"],
        check=True,
    )

    missing_exports = [name for name in EXPECTED_EXPORTS if not (EXPORT_DIR / name).exists()]
    if missing_exports:
        raise SystemExit(f"Missing Power BI exports: {missing_exports}")

    missing_screenshots = [
        name for name in EXPECTED_SCREENSHOTS if not (SCREENSHOT_DIR / name).exists()
    ]
    if missing_screenshots:
        raise SystemExit(f"Missing Power BI screenshots: {missing_screenshots}")

    telemetry_rows = _csv_count(EXPORT_DIR / "telemetry_samples.csv")
    health_rows = _csv_count(EXPORT_DIR / "health_scores.csv")
    if telemetry_rows != 264 or health_rows != 3:
        raise SystemExit(
            f"Unexpected Power BI export counts: telemetry={telemetry_rows}, health={health_rows}"
        )

    for path in (
        ROOT / "powerbi" / "README.md",
        ROOT / "powerbi" / "report_manifest.json",
        ROOT / "powerbi" / "corvus_powerbi_theme.json",
        ROOT / "docs" / "ACCESS_MANIFEST.md",
    ):
        if not path.exists():
            raise SystemExit(f"Missing Phase 4 artifact: {path}")

    print("Phase 4 Power BI report pack OK")


def _csv_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _row in csv.DictReader(handle))


if __name__ == "__main__":
    main()
