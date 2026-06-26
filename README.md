# Corvus

Agentic OBD-II performance and maintenance analyzer.

**Live demo target:** https://uhchi-actual.github.io/corvus/

Corvus reads diagnostic trouble codes and engine telemetry, stores the drive in a
relational model, runs all numeric analysis in SQL, then uses Huginn and Muninn
to explain SQL output in plain language.

## Current Status

Phase 4 Power BI report pack is in place:

- Backend FastAPI health scaffold.
- Frontend Next.js 15 static shell with uhchi design tokens.
- Docker Compose wrappers for local development.
- GitHub Actions for CI and GitHub Pages static export.
- Environment example, security notes, and phase guardrails.
- Normalized SQLite schema from the handoff.
- CSV and emulator CSV ingestion paths.
- Read-only live python-OBD adapter scaffold.
- Synthetic seed logs and a seeded SQLite database.
- Public KIT/RADAR OBD-II seed slice from a CC BY 4.0 dataset.
- Showcase SQL for baseline deviation, fuel-trim drift, and DTC-to-telemetry
  correlation.
- Deterministic session health score computed in SQL from editable directional
  scoring config.
- Huginn and Muninn LangGraph flow that explains SQL output and writes traced
  findings.
- Power BI-ready report pack against the seeded SQLite database.
- Smooth v1 shell with warm off-white accents and reduced-motion support.

The real static dashboard is reserved for Phase 5.

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
python scripts/check_phase0.py
python scripts/check_phase1.py
python scripts/check_phase2.py
python scripts/check_phase3.py
python scripts/check_phase4.py
cd backend && pytest -q && ruff check src tests
cd frontend && npm run lint && npm run build
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
- `frontend/src/app/` - Next.js static shell and future dashboard.
- `data/schema.sql` - normalized SQLite schema.
- `data/queries/` - showcase SQL and session health score query.
- `data/health_score_config.json` - editable directional scoring defaults.
- `data/seed/` - synthetic sample logs and seeded SQLite database.
- `docs/DATASETS.md` - public OBD-II source attribution and refresh notes.
- `docs/ACCESS_MANIFEST.md` - exact runtime entry points and OBD-II read scope.
- `powerbi/` - Phase 4 report pack, exports, theme, measures, and screenshots.
- `docs/` - guardrails, design notes, and deployment notes.

## Source Of Truth

This repo includes the build handoff as [HANDOFF.md](HANDOFF.md). Phase order and
architecture should follow that document unless it is explicitly revised.
