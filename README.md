# Corvus

SQL-first OBD-II performance and maintenance analyzer.

**Live demo:** https://uhchi-actual.github.io/corvus/

Corvus reads diagnostic trouble codes and engine telemetry, stores the drive in a
relational model, runs all numeric analysis in SQL, then uses Huginn and Muninn
to explain SQL output in plain language.

## Current Status

Phase 5 static dashboard is in place. Phase 6 readability polish is in place:

- Backend FastAPI health scaffold.
- Frontend Next.js 15 static dashboard with uhchi design tokens.
- Docker Compose wrappers for local development.
- GitHub Actions for CI and GitHub Pages static export.
- Environment example, security notes, and phase guardrails.
- Normalized SQLite schema from the handoff.
- CSV and emulator CSV ingestion paths.
- Read-only live python-OBD adapter scaffold.
- Synthetic seed logs and a seeded SQLite database.
- Public dashboard entries from KIT/RADAR (CC BY 4.0) and VED (Apache 2.0).
- Showcase SQL for baseline deviation, fuel-trim drift, and DTC-to-telemetry
  correlation.
- Deterministic session health score computed in SQL from editable directional
  scoring config.
- Huginn and Muninn LangGraph flow that explains SQL output and writes traced
  findings.
- Power BI-ready report pack against the seeded SQLite database.
- Smooth v1 dashboard with warm off-white accents, car inspiration material,
  and reduced-motion support.
- Public v1 mass-air-flow trend from real public OBD-II telemetry.
- Synthetic rows remain internal control data. Public dashboard rows are three
  real vehicles with exact source filenames and trip identifiers in the UI.

## Guardrails

- SQL computes every sensor value, deviation, trim figure, score, and
  correlation. LLM paths explain SQL output only.
- OBD-II specifics must be verified against the `brendan-w/python-OBD` source
  before implementation.
- Performance thresholds are directional defaults stored as editable config and
  must be labeled directional in the UI.
- Corvus is read-only: Mode 01, 02, 03, 07, and 09 reads are allowed. Mode 04
  clearing and ECU writes are out of scope.

Directional diagnostic guidance based on logged data - not a substitute for
inspection by a certified technician.

## Resume bullets

- Built an OBD-II vehicle-health analyzer: ingested live engine telemetry and
  diagnostic trouble codes, modeled them in a normalized SQL schema, and computed
  baseline-deviation metrics with SQL window functions.
- Designed a Power BI report pack and static dashboard surfacing mass-air-flow
  trends, fault-to-telemetry correlation, and per-drive health scores from public
  OBD-II logs.
- Added a LangGraph layer (Huginn and Muninn) that explains SQL-computed facts and
  ranks likely faults with trace ids, keeping all numeric analysis deterministic.

## Method

- Normalize OBD-II logs into one SQLite schema.
- Run deviation, drift, correlation, and scoring in SQL.
- Keep thresholds editable and labeled directional.
- Use Huginn and Muninn to summarize SQL output.
- Store trace IDs with each finding.

## Local Development

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the static frontend shell:

```bash
cd frontend
npm run dev
```

Run the backend scaffold:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

Run a local analysis pass:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/session/1?use_llm=false"
```

Run local checks:

```bash
python scripts/check_all.py
```

Export static dashboard data:

```bash
python scripts/export_frontend_dashboard.py --refresh-db
```

Seed the demo database:

```bash
python scripts/seed_database.py
```

## Docker

```bash
docker compose up --build
```

Before heavy Docker use on WSL2, cap the VHDX in `~/.wslconfig`:

```ini
[wsl2]
disk=40GB
```

See [docs/DOCKER_WSL2_DISK_CAP.md](docs/DOCKER_WSL2_DISK_CAP.md).

## Repository Map

- `backend/src/` - FastAPI scaffold, ingest, SQL, and agent modules.
- `backend/src/agent/` - Huginn and Muninn LangGraph analysis layer.
- `frontend/src/app/` - Next.js static dashboard.
- `frontend/src/data/dashboard.json` - static dashboard payload.
- `data/schema.sql` - normalized SQLite schema.
- `data/queries/` - showcase SQL and session health score query.
- `data/health_score_config.json` - editable directional scoring defaults.
- `data/seed/` - synthetic sample logs and seeded SQLite database.
- `docs/DATASETS.md` - public OBD-II source attribution and refresh notes.
- `docs/ACCESS_MANIFEST.md` - exact runtime entry points and OBD-II read scope.
- `docs/ASSETS.md` - dashboard image asset notes.
- `docs/INSTALL.md` - local install list and launch commands.
- `docs/METHODOLOGY.md` - terse data and analysis method.
- `powerbi/` - Phase 4 report pack, exports, theme, measures, and screenshots.
- `docs/` - guardrails, design notes, and deployment notes.

## Source Of Truth

This repo includes the build handoff as [HANDOFF.md](HANDOFF.md). Phase order and
architecture should follow that document unless it is explicitly revised.
