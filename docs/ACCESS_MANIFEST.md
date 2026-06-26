# Access Manifest

Corvus v1 is read-only.

## Runtime Entry Points

- `backend/src/ingest/csv_adapter.py::ingest_drive_csv`
- `backend/src/ingest/emulator_adapter.py::ingest_emulator_csv`
- `backend/src/ingest/live_obd.py::capture_live_session`
- `backend/src/agent/graph.py::analyze_session`
- `POST /analysis/session/{session_id}`

## Live OBD-II Commands

Verified against `brendan-w/python-OBD` commit
`a378bdd81d58c67d08050e4244173a9a7dbda73d`.

| Mode | python-OBD command | PID / service | Stored column |
| --- | --- | --- | --- |
| 01 | `RPM` | `010C` | `rpm` |
| 01 | `SPEED` | `010D` | `speed_kph` |
| 01 | `ENGINE_LOAD` | `0104` | `engine_load_pct` |
| 01 | `COOLANT_TEMP` | `0105` | `coolant_temp_c` |
| 01 | `INTAKE_TEMP` | `010F` | `intake_temp_c` |
| 01 | `MAF` | `0110` | `maf_gps` |
| 01 | `THROTTLE_POS` | `0111` | `throttle_pct` |
| 01 | `SHORT_FUEL_TRIM_1` | `0106` | `stft_b1_pct` |
| 01 | `LONG_FUEL_TRIM_1` | `0107` | `ltft_b1_pct` |
| 01 | `TIMING_ADVANCE` | `010E` | `timing_adv_deg` |
| 01 | `FUEL_PRESSURE` | `010A` | `fuel_press_kpa` |
| 01 | `O2_B1S1` | `0114` | `o2_b1s1_v` |
| 03 | `GET_DTC` | `03` | `dtc_events` |
| 07 | `GET_CURRENT_DTC` | `07` | `dtc_events` |
| 09 | `VIN` | `0902` | `vehicles.vin` |

`CLEAR_DTC` is Mode 04 in python-OBD and is not called.

## Public Dataset

- Source: Marc Weber, Automotive OBD-II Dataset, Karlsruhe Institute of
  Technology, 2023
- DOI: https://doi.org/10.35097/1130
- License: CC BY 4.0
- Archive checksum: `22d9aac00d1a2b4c97aa35fd7a103ba4`
- Local slice: `data/seed/public_obd_kit_sample.csv`

The fetch script verifies the published checksum before normalizing the sample.
