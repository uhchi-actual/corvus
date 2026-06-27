# Datasets

Corvus ships synthetic seed logs plus normalized slices from public OBD-II archives.

## KIT/RADAR Automotive OBD-II Dataset

- Source: Marc Weber, Automotive OBD-II Dataset, Karlsruhe Institute of Technology, 2023
- DOI: https://doi.org/10.35097/1130
- Repository page: https://www.radar-service.eu/radar/en/dataset/bCtGxdTklQlfQcAq
- License: CC BY 4.0
- Dashboard vehicle: Seat Leon
- Dashboard source files:
  - `2018-03-26_Seat_Leon_S_RT_Stau.csv` — warm traffic jam (good fit)
  - `2018-03-21_Seat_Leon_KA_RT_Normal.csv` — cold start (coolant below warm band)

`scripts/fetch_public_obd_dataset.py` downloads the archive, extracts the source CSV,
forward-fills staggered PID rows, and writes `data/seed/public_obd_kit_normal.csv`.

Scores use fixed warm-engine reference bands so a cold or mixed drive does not read as a
perfect 100 against a band derived from the same log.

## Vehicle Energy Dataset (VED)

- Source: Geunseob Oh, David J. LeBlanc, Huei Peng, Vehicle Energy Dataset (VED)
- Paper: https://doi.org/10.1109/TITS.2020.3035596
- Repository: https://github.com/gsoh/VED
- License: Apache 2.0
- Dashboard vehicles: VED ICE 6.0L V8 (VehId 108), VED Car 1.5L (VehId 8)
- Dashboard source file: `VED_171101_week.csv` with trip identifiers in session notes

The published week export includes RPM, speed, load, MAF, fuel trims, and ambient air
temperature (`OAT`). It does **not** include engine coolant temperature, so coolant
baseline panels are omitted when no samples exist.

`scripts/fetch_ved_dataset.py` clones the VED repository, extracts one week CSV from
Part 1, and writes tracked seed slices under `data/seed/`.

VED participant vehicles are de-identified. Corvus stores engine configuration labels
from the published static metadata, not owner make or model names.

## Refresh public seeds

```bash
python scripts/fetch_public_obd_dataset.py --all-dashboard-seeds
python scripts/fetch_ved_dataset.py --all-dashboard-seeds
python scripts/seed_database.py
```

The public dashboard displays only real public entries. Synthetic rows remain in the
database as internal control data for tests and baseline behavior.

Public v1 charts mass air flow. KIT rows omit fuel-trim fields. VED rows include
fuel trim from the published week logs.
