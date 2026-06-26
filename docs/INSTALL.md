# Install

Required:

- Python 3.12
- Node.js 22
- npm
- Git
- GitHub CLI

Recommended:

- Docker Desktop with Linux engine enabled
- Power BI Desktop
- ELM327 adapter for live capture

Python:

```bash
cd backend
pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm ci
```

Checks:

```bash
python scripts/check_all.py
```

Docker:

```bash
docker compose config
docker compose build
```

Docker Desktop must be running with the Linux engine before `docker compose build`.

Power BI:

```bash
python scripts/export_powerbi_dataset.py --refresh-db
```

Open `powerbi/README.md` for Desktop steps.
