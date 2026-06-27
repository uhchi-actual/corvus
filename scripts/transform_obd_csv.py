"""Fuzzy-map an arbitrary public OBD-II CSV into the Corvus canonical schema.

Usage:
    python scripts/transform_obd_csv.py INPUT.csv data/seed/public_obd_<slug>.csv \
        --rows 240 --warm-coolant 80

It auto-detects common column-name variants (rpm, speed, engine load, coolant,
intake temp, maf, throttle, short/long fuel trim, timing advance), generates 1 Hz
ISO timestamps, and writes a warm-running 240-row slice in the exact 16-column
order the ingester expects. Unmapped metrics are left blank (handled gracefully).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import re

# ruff: noqa: E701, E702, E722

CANON = ["ts","rpm","speed_kph","engine_load_pct","coolant_temp_c","intake_temp_c",
         "maf_gps","throttle_pct","stft_b1_pct","ltft_b1_pct","timing_adv_deg",
         "fuel_press_kpa","o2_b1s1_v","dtc_code","dtc_status","dtc_description"]

# canonical -> list of lowercase substrings to match against source headers
ALIASES = {
    "rpm": ["engine_rpm","rpm","engine speed"],
    "speed_kph": ["vehicle_speed","speed_kph","speed_kmh","speed (","vehicle speed","speed"],
    "engine_load_pct": ["engine_load","calculated_load","load_pct","engine load","load"],
    "coolant_temp_c": ["coolant_temp","coolant","ect","engine_coolant"],
    "intake_temp_c": ["intake_air_temp","intake_temp","iat","intake air"],
    "maf_gps": ["maf","mass_air_flow","air_flow","airflow"],
    "throttle_pct": ["relative_throttle","throttle_pos","throttle ("," throttle","throttle"],
    "stft_b1_pct": ["short_term_fuel_trim_bank_1","short_term_fuel_trim","stft","short term fuel"],
    "ltft_b1_pct": ["long_term_fuel_trim_bank_1","long_term_fuel_trim","ltft","long term fuel"],
    "timing_adv_deg": ["timing_advance","timing_adv","ignition_timing","timing"],
}

def _norm(h): return re.sub(r"\s+"," ",h.strip().lower())

def _build_map(headers):
    nmap = {h: _norm(h) for h in headers if h}
    chosen = {}
    for canon, subs in ALIASES.items():
        for sub in subs:                       # earlier substrings = stronger match
            hit = next((h for h,n in nmap.items() if n.startswith(sub) or n==sub or sub in n), None)
            if hit:
                chosen[canon] = hit
                break
    return chosen

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--rows", type=int, default=240)
    ap.add_argument("--warm-coolant", type=float, default=80.0)
    ap.add_argument("--start", type=str, default="2018-06-01T10:00:00")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.input)))
    cmap = _build_map(rows[0].keys())
    print("Detected column map:")
    for c in CANON:
        if c in cmap: print(f"  {c:16} <- {cmap[c]!r}")
    def val(r,c):
        h = cmap.get(c)
        if not h: return ""
        v = str(r.get(h,"")).strip()
        return "" if v in ("","nan","NaN","None") else v
    def coolant(r):
        v = val(r, "coolant_temp_c")
        try: return float(v)
        except: return 0.0
    # pick first warm, partly-moving window
    start = 0
    for i in range(0, max(1,len(rows)-a.rows)):
        win = rows[i:i+a.rows]
        warm = sum(1 for r in win if coolant(r) >= a.warm_coolant)
        if "coolant_temp_c" not in cmap or warm >= int(0.9*a.rows):
            start = i
            break
    win = rows[start:start+a.rows]
    base = datetime.datetime.fromisoformat(a.start)
    w = csv.writer(open(a.output,"w",newline=""))
    w.writerow(CANON)
    for j,r in enumerate(win):
        ts = (base+datetime.timedelta(seconds=j)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        w.writerow([ts]+[val(r,c) for c in CANON[1:]])
    print(f"\nWrote {len(win)} rows -> {a.output} (start idx {start})")

if __name__ == "__main__":
    main()
