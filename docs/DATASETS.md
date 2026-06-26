# Datasets

Corvus ships synthetic seed logs plus a small normalized slice from a public
OBD-II dataset.

## Public OBD-II Seed

- Source: Marc Weber, Automotive OBD-II Dataset, Karlsruhe Institute of
  Technology, 2023
- DOI: https://doi.org/10.35097/1130
- Repository page: https://www.radar-service.eu/radar/en/dataset/bCtGxdTklQlfQcAq
- License: CC BY 4.0
- Dashboard source vehicle: Seat Leon
- Dashboard source files:
  - `2018-02-23_Seat_Leon_RT_RT_Frei_Beschleunigung.csv`
  - `2018-03-21_Seat_Leon_KA_RT_Normal.csv`
  - `2018-02-18_Seat_Leon_RT_KA_Stau.csv`
- Legacy seed source file: `2018-03-29_Seat_Leon_KA_RT_Stau.csv`

The upstream archive contains OBD Auto Doctor CSV logs with ten OBD-II signals.
`scripts/fetch_public_obd_dataset.py` downloads the archive, extracts selected
source CSV files, forward-fills staggered PID rows, and writes tracked Corvus
seed slices under `data/seed/`.

The script does not interpolate sensor values. It only carries forward the last
reported PID value so the row-oriented Corvus schema can ingest the log.

The public dashboard displays only real public entries. Synthetic rows remain in
the database as internal control data for tests and baseline behavior.
The selected public files include mass air flow, RPM, speed, coolant, intake
temperature, and throttle. They do not include fuel-trim fields, so public v1
charts mass air flow instead of filling missing trim values.

Refresh the public seed:

```bash
python scripts/fetch_public_obd_dataset.py --all-dashboard-seeds
python scripts/seed_database.py
```
