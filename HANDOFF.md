# Corvus — Build Handoff

> **Project name: Corvus** (slug `corvus`). The name is *corvus* — Latin for raven —
> nodding to Odin's reporting ravens, the Corvus constellation (consistent with the
> Ultraviolet/Laniakea naming line), and sharing its root with **Corvette**.
> The two analysis agents are named **Huginn** and **Muninn**, Odin's ravens
> ("Thought" and "Memory"): they range over the data, observe, and report back.

**Target repo:** `github.com/uhchi-actual/corvus` (public)
**Live demo (Pages):** `https://uhchi-actual.github.io/corvus/`
**One-liner:** Agentic OBD-II performance and maintenance analyzer — reads trouble codes and live engine telemetry, compares each drive against a per-vehicle baseline in SQL, and outputs ranked likely faults with the evidence and recommended fixes.

This document is the build spec. It is written so a coding agent (Cursor/Codex) or you can build the repo phase by phase without inventing anything. Every OBD-II fact here is from the python-OBD source and the SAE J1979 PID reference — verify against those, not memory, if anything looks off.

---

## 0. What this is and why it screams "Data Analyst"

A recruiter screening for a data analyst wants to see: messy real-world data → a relational model → SQL that produces insight → a dashboard that a non-technical person can read. This project is built around that spine on purpose.

- **Messy source data:** raw OBD-II telemetry (5–10 samples/sec, unit-bearing, noisy) plus diagnostic trouble codes (DTCs).
- **Relational model:** a normalized SQL schema (vehicles → sessions → telemetry/DTC events → baselines → findings).
- **SQL that produces insight:** window functions and baseline joins compute deviation, sustained fuel-trim drift, and DTC-to-telemetry correlation. **The numbers are computed in SQL, never by the LLM.**
- **Dashboard:** a Power BI report (the resume keyword) plus an interactive web dashboard that is the public live demo.
- **The agentic layer** sits on top and only *explains* the SQL output in plain language and ranks likely fixes. It is the differentiator, not the foundation.

The pitch line for the README and resume: *"Took raw engine telemetry and fault codes, modeled them in SQL, and built a baseline-deviation engine plus a Power BI dashboard that surfaces the most likely fault and fix for a given drive."*

---

## 1. Architecture

```
                 ┌─────────────────────────────────────────────┐
   DATA IN       │  INGEST (deterministic, Python)             │
   ───────       │  • Live: python-OBD over ELM327 (USB/BT/WiFi)│
   ELM327 ──────►│  • CSV: Torque Pro / Car Scanner exports    │
   CSV logs ────►│  • Demo: ELM327-emulator (no hardware)      │
   emulator ────►│  → normalize to tidy rows                   │
                 └───────────────────┬─────────────────────────┘
                                     ▼
                 ┌─────────────────────────────────────────────┐
   STORE + MATH  │  SQL (SQLite dev / Postgres optional)       │
   ────────────  │  • schema: vehicles, drive_sessions,        │
                 │    telemetry_samples, dtc_events,           │
                 │    baselines, findings                      │
                 │  • baseline-deviation queries (window fns)  │  ◄── the DA core
                 │  • DTC↔telemetry correlation joins          │
                 └───────────────────┬─────────────────────────┘
                                     ▼
                 ┌─────────────────────────────────────────────┐
   LANGUAGE      │  AGENT (LangGraph) — explains, never computes│
   ────────      │  dtc_interpreter → correlation →            │
                 │  recommendation → report_writer             │
                 │  LLM: provider-agnostic (Ollama local OK)   │
                 └───────────────────┬─────────────────────────┘
                                     ▼
                 ┌──────────────────────┬──────────────────────┐
   OUT           │  Power BI (.pbix)    │  Next.js static demo │
                 │  + Publish-to-web    │  → GitHub Pages       │
                 └──────────────────────┴──────────────────────┘
```

**Why the deterministic/LLM split:** SQL computes every deviation, trim average, and correlation. The LangGraph agent receives those numbers as facts and only writes the interpretation ("LTFT sustained at +14% under cruise → lean condition; likely vacuum leak, weak fuel pump, or dirty MAF"). The LLM cannot fabricate a sensor reading because it never touches raw telemetry. This is the same architecture as GRAiD's deterministic math engine + language layer.

---

## 2. Data sources (verified)

| Source | Library / format | Use | Notes |
|---|---|---|---|
| Live ELM327 adapter | `python-OBD` (`brendan-w/python-OBD`) | real car capture | `obd.OBD()` auto-connects; `connection.query(obd.commands.RPM)` returns Pint unit-bearing values. ELM327 ≈ 5–10 PIDs/sec. |
| CSV drive logs | Torque Pro / Car Scanner CSV export | offline analysis | Standard hobbyist export format; lets you build/test with no live car. |
| No-hardware demo | `Ircama/ELM327-emulator` | CI + live demo data | Simulates an ECU; `obd_dictionary` can also ingest Torque CSVs to build a realistic scenario. This feeds the public demo so it works without a car. |

**OBD-II modes used (from python-OBD source):**
- **Mode 01** — live current data (PIDs). e.g. `RPM` (`010C`), `SPEED`, `ENGINE_LOAD` (`0104`), `COOLANT_TEMP` (`0105`), `SHORT_FUEL_TRIM_1` (`0106`), `FUEL_STATUS` (`0103`).
- **Mode 02** — freeze-frame snapshot at the moment a DTC set (prefix `DTC_` on the Mode 01 name).
- **Mode 03** — `GET_DTC`: stored trouble codes.
- **Mode 07** — `GET_CURRENT_DTC`: pending codes from the current drive cycle.
- **Mode 09** — `VIN`, calibration IDs (vehicle identity).

> Legal note for the README: reading your own vehicle's OBD-II data is legal; the port is federally mandated for independent diagnostics. Clearing codes (Mode 04) is intentionally **out of scope** — this tool reads and analyzes only, it does not write to the ECU.

---

## 3. SQL schema

SQLite for dev (zero-config, ships in the repo as a seeded `.db`); Postgres optional via the same DDL with minor type swaps. Keep the DDL in `data/schema.sql`.

```sql
CREATE TABLE vehicles (
  vehicle_id   INTEGER PRIMARY KEY,
  vin          TEXT,
  make         TEXT,
  model        TEXT,
  year         INTEGER,
  engine       TEXT,          -- e.g. 'LS1 5.7L V8'
  notes        TEXT
);

CREATE TABLE drive_sessions (
  session_id   INTEGER PRIMARY KEY,
  vehicle_id   INTEGER REFERENCES vehicles(vehicle_id),
  started_at   TIMESTAMP,
  ended_at     TIMESTAMP,
  source       TEXT,          -- 'live' | 'csv' | 'emulator'
  ambient_c    REAL,
  notes        TEXT
);

CREATE TABLE telemetry_samples (
  sample_id        INTEGER PRIMARY KEY,
  session_id       INTEGER REFERENCES drive_sessions(session_id),
  ts               TIMESTAMP,
  rpm              REAL,
  speed_kph        REAL,
  engine_load_pct  REAL,
  coolant_temp_c   REAL,
  intake_temp_c    REAL,
  maf_gps          REAL,      -- grams/sec
  throttle_pct     REAL,
  stft_b1_pct      REAL,      -- short-term fuel trim bank 1
  ltft_b1_pct      REAL,      -- long-term fuel trim bank 1
  timing_adv_deg   REAL,
  fuel_press_kpa   REAL,
  o2_b1s1_v        REAL
);

CREATE TABLE dtc_events (
  dtc_id      INTEGER PRIMARY KEY,
  session_id  INTEGER REFERENCES drive_sessions(session_id),
  ts          TIMESTAMP,
  code        TEXT,           -- 'P0301'
  status      TEXT,           -- 'stored' | 'pending' | 'permanent'
  description TEXT
);

-- per-vehicle healthy ranges, keyed by operating context
CREATE TABLE baselines (
  baseline_id  INTEGER PRIMARY KEY,
  vehicle_id   INTEGER REFERENCES vehicles(vehicle_id),
  metric       TEXT,          -- 'coolant_temp_c', 'ltft_b1_pct', ...
  context      TEXT,          -- 'idle' | 'cruise' | 'wot' | 'cold' | 'warm'
  healthy_min  REAL,
  healthy_max  REAL,
  unit         TEXT,
  source       TEXT           -- 'spec' | 'observed' | 'manual'
);

-- agent output, one row per detected issue
CREATE TABLE findings (
  finding_id      INTEGER PRIMARY KEY,
  session_id      INTEGER REFERENCES drive_sessions(session_id),
  severity        TEXT,        -- 'info' | 'watch' | 'fault'
  category        TEXT,        -- 'fueling' | 'cooling' | 'misfire' | ...
  metric_or_code  TEXT,
  observed        TEXT,
  expected_range  TEXT,
  likely_cause    TEXT,
  recommended_fix TEXT,
  confidence      REAL,
  evidence_json   TEXT,        -- the SQL rows that triggered this
  agent_trace_id  TEXT,
  created_at      TIMESTAMP
);
```

### Showcase queries (put these in `data/queries/` and reference them in the README)

**A. Baseline deviation — % of a session each metric spent out of healthy range:**
```sql
SELECT b.metric, b.context,
       ROUND(100.0 * SUM(CASE WHEN t.coolant_temp_c NOT BETWEEN b.healthy_min AND b.healthy_max
                              THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_out_of_range
FROM telemetry_samples t
JOIN drive_sessions s   ON s.session_id = t.session_id
JOIN baselines b        ON b.vehicle_id = s.vehicle_id
                       AND b.metric = 'coolant_temp_c'
WHERE t.session_id = :session_id
GROUP BY b.metric, b.context;
```

**B. Sustained fuel-trim drift — rolling average to separate a real lean/rich condition from noise:**
```sql
SELECT ts,
       AVG(ltft_b1_pct) OVER (ORDER BY ts ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) AS ltft_30s
FROM telemetry_samples
WHERE session_id = :session_id
ORDER BY ts;
```

**C. DTC ↔ telemetry correlation — pull the telemetry window around each fault:**
```sql
SELECT d.code, d.ts AS fault_ts, t.ts, t.rpm, t.engine_load_pct, t.coolant_temp_c
FROM dtc_events d
JOIN telemetry_samples t
  ON t.session_id = d.session_id
 AND t.ts BETWEEN datetime(d.ts, '-5 seconds') AND datetime(d.ts, '+5 seconds')
WHERE d.session_id = :session_id
ORDER BY d.code, t.ts;
```

---

## 4. Performance markers (directional rules — tune per engine, do not hard-code as truth)

These are common diagnostic heuristics, not guarantees. Store them as editable rows in `baselines`/a rules file so the analyst (you) owns the thresholds. **Label them as directional in the UI.** Validate against your actual vehicle before trusting any single one.

| Marker | Rule of thumb | Directional reading |
|---|---|---|
| Long-term fuel trim | sustained beyond roughly ±10% | lean (+): vacuum leak / weak pump / dirty MAF · rich (−): leaking injector / MAF / O2 |
| Coolant temp | above the warm-running baseline band | cooling system (thermostat, coolant, fan, water pump) |
| Misfire codes | P0300 (random) / P030x (cylinder x), correlated with load/RPM | ignition, fuel delivery, or mechanical on the named cylinder |
| Engine load at idle | elevated vs. idle baseline | accessory drag, timing, or intake issue |
| Timing advance / knock retard | recurring retard under load | knock — fuel quality, carbon, or sensor |

The agent's job is to combine a DTC with its telemetry evidence and the baseline deviation, then output a *ranked* list with confidence — never a single confident verdict.

---

## 5. Agent graph (LangGraph)

Two named agents under the Corvus system, mapped to Odin's ravens. Naming is
organizational — the deterministic/LLM split still holds: **SQL computes, the agents
explain.** Neither raven computes a sensor value.

**Huginn ("Thought") — the present.** Handles the live/current drive: ingest,
real-time telemetry deviation, and code interpretation for the session in front of it.

**Muninn ("Memory") — the past.** Owns the per-vehicle baseline and history: recalls
what "normal" looks like for this car, correlates the current findings against it, and
produces the ranked recommendation from accumulated memory.

Nodes (deterministic nodes have no LLM call):

1. **`ingest_normalizer`** *(deterministic — Huginn)* — raw OBD/CSV → tidy rows → DB.
2. **`sql_deviation`** *(deterministic — Huginn)* — runs the showcase queries, returns structured deviation facts.
3. **`dtc_interpreter`** *(LLM + lookup table — Huginn)* — maps each code to system + plain-English meaning. Codes come from a local lookup first; LLM only fills narrative.
4. **`baseline_recall`** *(deterministic — Muninn)* — loads the per-vehicle baseline ranges and prior-session norms for comparison.
5. **`correlation`** *(deterministic + LLM — Muninn)* — joins DTCs to their telemetry window (query C) and against baseline; LLM summarizes the pattern.
6. **`recommendation`** *(LLM — Muninn)* — ranked likely causes + fixes, each with confidence and the evidence rows it used.
7. **`report_writer`** *(deterministic — Corvus core)* — writes `findings` rows (with `agent_trace_id`) and the dashboard payload.

Reuse your Stratgyk Agent-13 conventions:
- **Provider-agnostic LLM env vars:** `LLM_API_KEY`, `LLM_ENDPOINT`, `LLM_MODEL`, `USE_LLM`. Works with local Ollama (`JOSIEFIED-Qwen3:8b`) or a hosted model with no code change.
- **Mandatory disclaimer on every response path** (including errors): *"Directional diagnostic guidance based on logged data — not a substitute for inspection by a certified technician."*
- **`agent_trace` written before output**, `agent_trace_id` returned with each finding.

---

## 6. Repository layout (mirrors Ultraviolet)

```
corvus/
├── .github/workflows/
│   ├── pages.yml            # build static frontend → GitHub Pages
│   └── ci.yml               # lint + tests + emulator smoke run
├── backend/
│   ├── src/
│   │   ├── ingest/          # python-OBD live + CSV + emulator adapters
│   │   ├── sql/             # query runners
│   │   ├── agent/           # LangGraph nodes
│   │   └── main.py          # FastAPI
│   └── pyproject.toml
├── frontend/                # Next.js 15, static export, uhchi theme
│   └── src/app/
├── data/
│   ├── schema.sql
│   ├── seed/                # sample drive logs (CSV) + seeded corvus.db
│   └── queries/             # showcase .sql files
├── powerbi/
│   ├── corvus.pbix
│   └── screenshots/
├── docs/
├── README.md
├── HANDOFF.md
├── SECURITY.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## 7. Build phases

- **Phase 0 — scaffold:** repo, `.gitignore`, Docker, CI, Pages enabled. (See Docker disk warning below.)
- **Phase 1 — ingest + schema:** CSV and emulator paths first (no car needed), then live `python-OBD`. Load `schema.sql`, seed sample logs.
- **Phase 2 — SQL core:** the three showcase queries + a session health score. This is the DA centerpiece — make it shine.
- **Phase 3 — agent:** LangGraph graph, provider-agnostic LLM, disclaimer + trace.
- **Phase 4 — Power BI:** connect to the SQLite/Postgres DB, build deviation + DTC + fuel-trim pages, export `.pbix`, Publish-to-web for the link.
- **Phase 5 — web demo:** Next.js static dashboard reading the seeded findings, uhchi-themed, deployed to Pages. This is the live demo.
- **Phase 6 — polish:** README, screenshots, resume bullets.

---

## 8. Environment (`.env.example`)

```
# LLM (provider-agnostic — local Ollama by default)
USE_LLM=true
LLM_ENDPOINT=http://localhost:11434/v1
LLM_MODEL=JOSIEFIED-Qwen3:8b
LLM_API_KEY=not-needed-for-local

# Data
DATABASE_URL=sqlite:///data/seed/corvus.db
OBD_PORT=auto        # 'auto' lets python-OBD find the adapter; or e.g. /dev/ttyUSB0
```

---

## 9. Deployment

- **Frontend live demo:** `pages.yml` builds the Next.js static export and serves it at `uhchi-actual.github.io/corvus/` — identical pattern to Ultraviolet.
- **Power BI:** `.pbix` committed under `powerbi/`; use *Publish to web* for a public read-only link in the README. (Power BI / Tableau cannot embed in a static Pages site — keep the link, not an iframe.)
- **Backend:** runs locally or via `docker-compose up`. Not required for the live demo (the demo reads pre-seeded findings).

> **Docker disk warning (standing rule):** the WSL2 Docker VHDX grows and does not auto-shrink — a prior run hit ~45 GB. Cap it in `~/.wslconfig`:
> ```
> [wsl2]
> disk=40GB
> ```
> and prune regularly (`docker system prune -af --volumes`). On the RTX 5050's 8 GB VRAM, keep the local model at `JOSIEFIED-Qwen3:8b Q5_K_M` or smaller; the agent layer is light, so don't run heavier models alongside it.

---

## 10. Resume bullets (lift these once it's built)

- Built an OBD-II vehicle-health analyzer: ingested live engine telemetry and diagnostic trouble codes, modeled them in a normalized SQL schema, and computed baseline-deviation metrics with SQL window functions.
- Designed a Power BI dashboard surfacing fuel-trim drift, fault-to-telemetry correlation, and per-drive health scores from raw sensor logs.
- Added an agentic interpretation layer (LangGraph) that explains SQL-computed anomalies and ranks likely faults with confidence — keeping all numeric analysis deterministic for reliability.

---

## 11. Creating the public repo

The name is decided (**Corvus** / slug `corvus`) and already applied throughout this
doc — no find-replace needed. Create the public repo (owner runs this; the agent
cannot create it):

```bash
gh repo create uhchi-actual/corvus --public --source . --remote origin --push
# then in repo Settings → Pages → Source: GitHub Actions
```

If not using the `gh` CLI: create the empty public repo on github.com, then
`git remote add origin …`, push, and enable Pages → GitHub Actions in Settings.
