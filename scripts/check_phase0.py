from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
    ".env.example",
    ".gitignore",
    "HANDOFF.md",
    "README.md",
    "SECURITY.md",
    "docker-compose.yml",
    "backend/pyproject.toml",
    "backend/src/main.py",
    "backend/src/ingest",
    "backend/src/sql",
    "backend/src/agent",
    "frontend/package.json",
    "frontend/next.config.ts",
    "frontend/src/app/page.tsx",
    "data/schema.sql",
    "data/seed",
    "data/queries",
    "powerbi/screenshots",
    "backend/tests/helpers.py",
    "docs/DOCKER_WSL2_DISK_CAP.md",
    "docs/DESIGN.md",
    "docs/INSTALL.md",
    "docs/METHODOLOGY.md",
    "scripts/check_all.py",
]


def main() -> None:
    missing = [path for path in EXPECTED_PATHS if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing Phase 0 paths: {', '.join(missing)}")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ("USE_LLM", "LLM_ENDPOINT", "LLM_MODEL", "LLM_API_KEY", "DATABASE_URL", "OBD_PORT"):
        if f"{key}=" not in env_example:
            raise SystemExit(f"Missing .env.example key: {key}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "Mode 04" not in readme or "SQL computes" not in readme:
        raise SystemExit("README guardrails are incomplete")

    methodology = (ROOT / "docs/METHODOLOGY.md").read_text(encoding="utf-8")
    if "SQL does the numeric work" not in methodology or "agent_trace_id" not in methodology:
        raise SystemExit("Methodology doc is incomplete")

    dashboard = json.loads((ROOT / "frontend/src/data/dashboard.json").read_text(encoding="utf-8"))
    data_source = dashboard["dataSource"]
    licenses = {source["license"] for source in data_source.get("sources", [])}
    if "CC BY 4.0" not in licenses:
        raise SystemExit("Frontend public data attribution is missing CC BY 4.0 license")
    if len(data_source.get("sources", [])) < 3:
        raise SystemExit("Frontend public data attribution is missing a public archive source")

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    if "disk=40GB" not in compose:
        raise SystemExit("Docker Compose is missing the WSL2 disk cap warning")

    print("Phase 0 scaffold contract OK")


if __name__ == "__main__":
    main()
