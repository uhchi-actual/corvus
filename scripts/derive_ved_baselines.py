"""Transmute the two VED reference engines into per-class baseline bands.

VED entries stop being display vehicles and become the baseline library the
distance measure scores real drives against. We derive a robust healthy band
(P5-P95) per engine class for the metrics VED actually carries (engine_load_pct,
maf_gps). Coolant / fuel-trim / timing bands stay manual spec values because the
VED week export does not populate those PIDs.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed"

# engine class -> VED source slice
SOURCES = {
    "heavy": SEED / "public_obd_ved_6l_v8.csv",     # large displacement / V8 reference
    "light": SEED / "public_obd_ved_car_1p5l.csv",  # small displacement / economy reference
}
METRICS = ["engine_load_pct", "maf_gps"]

def _percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    i = min(len(sorted_vals) - 1, max(0, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[i]

def _band(path: Path, metric: str):
    vals = []
    for row in csv.DictReader(open(path)):
        raw = str(row.get(metric, "")).strip()
        if raw in ("", "nan", "NaN", "None"):
            continue
        vals.append(float(raw))
    vals.sort()
    if len(vals) < 10:
        return None
    return {
        "healthy_min": round(_percentile(vals, 5), 1),
        "healthy_max": round(_percentile(vals, 95), 1),
        "p50": round(_percentile(vals, 50), 1),
        "n": len(vals),
    }

def main():
    profiles = {}
    for cls, path in SOURCES.items():
        profiles[cls] = {"source_file": path.name}
        for m in METRICS:
            b = _band(path, m)
            if b:
                profiles[cls][m] = b
    out = ROOT / "data" / "ved_baseline_profiles.json"
    json.dump({"_note": "Per-engine-class baseline bands transmuted from VED reference engines (P5-P95).",
               "profiles": profiles}, open(out, "w"), indent=2)
    open(out, "a").write("\n")
    print(json.dumps(profiles, indent=2))

if __name__ == "__main__":
    main()
