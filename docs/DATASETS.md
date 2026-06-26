# Datasets

Corvus ships synthetic seed logs plus a small normalized slice from a public
OBD-II dataset.

## Public OBD-II Seed

- Source: Marc Weber, Automotive OBD-II Dataset, Karlsruhe Institute of
  Technology, 2023
- DOI: https://doi.org/10.35097/1130
- Repository page: https://www.radar-service.eu/radar/en/dataset/bCtGxdTklQlfQcAq
- License: CC BY 4.0
- Source file used: `2018-03-29_Seat_Leon_KA_RT_Stau.csv`

The upstream archive contains OBD Auto Doctor CSV logs with ten OBD-II signals.
`scripts/fetch_public_obd_dataset.py` downloads the archive, extracts the source
CSV, forward-fills staggered PID rows, and writes the tracked Corvus seed slice
at `data/seed/public_obd_kit_sample.csv`.

The script does not interpolate sensor values. It only carries forward the last
reported PID value so the row-oriented Corvus schema can ingest the log.

Refresh the public seed:

```bash
python scripts/fetch_public_obd_dataset.py
python scripts/seed_database.py
```
