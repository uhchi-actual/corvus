# Corvus — Diverse Vehicles + VED-as-Baseline (Master Work Order)

Verified against `main` @ `def9eea`. Two asks, answered:

1. **A more diverse output set** — replace the two VED display cars with two genuinely different open real cars, so the picker is three unique vehicles from three makes/regions.
2. **Repurpose the VED engines as baselines** — the two synthetic VED engine profiles become the per-engine-class baseline library the distance measure scores real drives against ("transmutation").

The hard parts (dataset research, baseline math, backend logic, one prepared real-car CSV) are **done and verified** below — the files are in the `corvus_dropin/` folder beside this doc. The mechanical wiring is the idiot-proof handoff in Section 4.

---

## 1. RECOMMENDATION — the two replacement cars

I checked licenses and data quality, not just names. Final three-car set:

| Slot | Vehicle | Source | Engine | License | Status |
|---|---|---|---|---|---|
| Keep | **Seat Leon** (Traffic Jam Log) | KIT/RADAR Automotive OBD-II (radar.kit.edu) | ~1.x petrol | CC BY 4.0 | already in repo |
| Replace VED #1 | **Toyota Etios 2014** | `github.com/eron93br/carOBD` | 1496cc / 1.5L | open, cite the thesis | **CSV prepared for you** |
| Replace VED #2 | **Opel Corsa 2012** (A12XER) | Kaggle `pedro2025/obd2-panel-opel-2012` | 1.2L | confirm on Kaggle data card | one download (Section 4.2) |

Why these: three different makes (Seat / Toyota / Opel), three regions (DE-collected / Brazil / Spain), all real logged OBD-II. The **Etios is richer than anything currently in the repo** — it carries real coolant, **both fuel trims, and timing advance** (the KIT Leon has none of the trims; VED had none either), so it actually exercises the Baseline Fit and Sensor Balance axes with real data.

**Rejected:** `YunSolutions/levin-openData` — conflicting CC BY-NC-SA / MIT license signals, NonCommercial terms (bad for a portfolio/resume piece), no per-vehicle engine identification, and data hosted off-GitHub (mega.nz). Not clean enough.

---

## 2. RECOMMENDATION — the VED→baseline transmutation (designed + verified)

**The idea.** The two VED slices stop being display cars and become a two-class baseline library. VED's usable real signal is `engine_load_pct` and `maf_gps` (its fuel-trim columns are all `NaN`), and the two engines show a clean fingerprint: the 6.0L V8 idles big and cruises at low load, the 1.5L works much harder. I derived a robust healthy band (P5–P95) per class from the **actual** VED CSVs:

| Class | `engine_load_pct` band | from |
|---|---|---|
| **heavy** (≥3.0L or V6/V8/V10/V12) | **11.4 – 38.8 %** | `public_obd_ved_6l_v8.csv` |
| **light** (everything else) | **14.5 – 81.2 %** | `public_obd_ved_car_1p5l.csv` |

At scoring time each real drive is matched to its class by engine displacement, and the VED-derived band for that class **replaces the old manual `engine_load` band (idle 12–35%)** in the existing `baseline_deviation.sql`. Everything else (coolant, trims, timing bands) stays as manual spec values, because VED can't inform them. This is a surgical one-row swap — no new SQL metric, no schema change, no frontend change.

**Why this is honest and exercises both VED engines.** I ran the full distance-measure chain on real data end-to-end:

- **Toyota Etios** (light) → engine_load scored vs the VED light band → 0% out of range (its 20–56% load fits), real trims 0% out, coolant 25.8% out, timing 81% out → a genuine, non-100 score driven by real telemetry.
- **LS1 5.7L V8 control** (already seeded) → classified **heavy** → engine_load scored vs the VED **V8** band → 41.7% out of range. So the heavy baseline does real work even though all three *public* cars are light.

Both VED engines are now load-bearing baselines, and nothing in the pipeline errored.

---

## 3. WHAT I ALREADY BUILT (drop these in as-is — all verified)

In `corvus_dropin/`, mirroring the repo layout:

- `data/seed/public_obd_caro_etios_1p5l.csv` — **prepared** 240-row warm-running Etios slice in the exact 16-column canonical schema. Verified to ingest and score.
- `data/ved_baseline_profiles.json` — the derived per-class bands (the table above), read at seed time.
- `scripts/derive_ved_baselines.py` — regenerates that JSON from the VED CSVs (reproducible; already run).
- `backend/src/ingest/baseline_profiles.py` — `engine_class()`, `engine_load_band()`, `baseline_source()`. Self-tested.
- `scripts/transform_obd_csv.py` — fuzzy-maps any public OBD CSV (e.g. the Corsa) into the canonical schema in one command. Smoke-tested.

---

## 4. IDIOT-PROOF HANDOFF (the easy, mechanical tasks)

Do these in order. After each, run `cd frontend && NEXT_PUBLIC_BASE_PATH=/corvus npm run build` only at the end (Section 4.6). Use exact strings.

### 4.1 — Drop in the five prepared files
Copy each file from `corvus_dropin/` to the same relative path in the repo. Do not edit them.

### 4.2 — Get the Opel Corsa CSV (the one manual download)
1. Open `https://www.kaggle.com/datasets/pedro2025/obd2-panel-opel-2012`. **Confirm the license on the data card is open** (CC/Public-domain). If it is not open, stop and tell the owner.
2. Download `dataset.csv`. From repo root run:
   ```
   python scripts/transform_obd_csv.py <path-to>/dataset.csv data/seed/public_obd_opel_corsa_1p2l.csv --rows 240 --warm-coolant 80
   ```
3. Confirm it printed a column map for at least rpm, speed, engine_load, and wrote 240 rows.

### 4.3 — Rewire the seed so VED is baseline-only and the two new cars are display cars
File: `scripts/seed_database.py`.

(a) **Remove** the two VED dicts from `PUBLIC_DRIVE_SOURCES` (the entries whose `seed_file` are `public_obd_ved_6l_v8.csv` and `public_obd_ved_car_1p5l.csv`). The VED CSVs stay on disk — they are now only the baseline source, not display cars. Also remove the second Seat Leon dict (`public_obd_kit_cold.csv`) if still present.

(b) **Add** these two dicts to `PUBLIC_DRIVE_SOURCES`:
```python
    {
        "seed_file": "public_obd_caro_etios_1p5l.csv",
        "source_file": "carOBD live1.csv (Toyota Etios 2014)",
        "label": "City Commute Log",
        "vehicle": VehicleMetadata(
            vin=None, make="Toyota", model="Etios 1.5L", year=2014,
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
            vin=None, make="Opel", model="Corsa 1.2L", year=2012,
            engine="4-FI 1.2L",
            notes="Public OBD2 panel Opel 2012 dataset (Kaggle pedro2025); A12XER 1.2L.",
        ),
        "dataset": "OBD2 panel Opel 2012",
        "license": "see Kaggle data card",
    },
```

(c) Make the reference-baseline call pass the engine. Change the public loop call from `insert_reference_baselines(conn, public_result.vehicle_id)` to:
```python
            insert_reference_baselines(conn, public_result.vehicle_id, source["vehicle"].engine)
```
and the two demo (LS1) calls from `insert_demo_baselines(conn, csv_result.vehicle_id)` / `insert_demo_baselines(conn, emulator_result.vehicle_id)` to pass `vehicle.engine`:
```python
        insert_demo_baselines(conn, csv_result.vehicle_id, vehicle.engine)
        ...
        insert_demo_baselines(conn, emulator_result.vehicle_id, vehicle.engine)
```

### 4.4 — Make `insert_reference_baselines` use the VED band
File: `backend/src/ingest/database.py`. At the top, add the import:
```python
from .baseline_profiles import engine_load_band, baseline_source
```
Replace the body of `insert_reference_baselines` (and update `insert_demo_baselines`) with:
```python
def insert_demo_baselines(conn, vehicle_id, engine=None):
    insert_reference_baselines(conn, vehicle_id, engine)


def insert_reference_baselines(conn, vehicle_id, engine=None):
    """Reference bands for scoring real logs. engine_load is VED-derived per class."""
    lo, hi = engine_load_band(engine)
    rows = [
        ("coolant_temp_c", "warm", 82.0, 105.0, "C", "manual"),
        ("ltft_b1_pct", "cruise", -10.0, 10.0, "%", "manual"),
        ("stft_b1_pct", "cruise", -10.0, 10.0, "%", "manual"),
        ("engine_load_pct", "class", lo, hi, "%", baseline_source(engine)),
        ("timing_adv_deg", "cruise", 10.0, 45.0, "deg", "manual"),
    ]
    conn.executemany(
        "INSERT INTO baselines (vehicle_id, metric, context, healthy_min, healthy_max, unit, source)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(vehicle_id, *row) for row in rows],
    )
```
Leave `insert_vehicle_baselines_from_session` untouched.

### 4.5 — Reseed and re-export
```
python scripts/derive_ved_baselines.py            # refreshes data/ved_baseline_profiles.json (already correct)
python scripts/seed_database.py                    # rebuilds data/seed/corvus.db
python scripts/export_frontend_dashboard.py        # rebuilds frontend dashboard.json
```

### 4.6 — Verify, then ship
1. `cd frontend && NEXT_PUBLIC_BASE_PATH=/corvus npm run build` → exit 0.
2. Picker shows exactly three vehicles: **Seat Leon, Toyota Etios 1.5L, Opel Corsa 1.2L**. No VED entry in the picker. No duplicate make.
3. Selecting the Etios shows a populated Baseline Fit and Sensor Balance (real trims), and a non-100 score.
4. `git commit -am "Diversify fleet: Toyota Etios + Opel Corsa; transmute VED engines into per-class baseline library"` then `git push origin main`; watch Actions → Deploy GitHub Pages go green; hard-refresh the live site.

---

## 5. DO NOT
- Do not seed VED as a display vehicle — it is baseline-only now. Keep the VED CSVs on disk (the derive script reads them).
- Do not hand-edit health scores or the derived bands; regenerate them with the scripts.
- Do not add a new metric to `baseline_deviation.sql` or change the schema — the transmutation is a band-source swap only.
- Do not invent a vehicle or fabricate a "V8" public car; open clean large-engine OBD data doesn't exist, which is exactly why the VED V8 is the *baseline* and the LS1 control consumes it.
- Do not ship the Corsa if its Kaggle license isn't open — tell the owner instead.
- Keep the fleet at three.
