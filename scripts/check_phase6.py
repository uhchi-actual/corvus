from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    page = (ROOT / "frontend/src/app/page.tsx").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend/src/components/dashboard/Dashboard.tsx").read_text(encoding="utf-8")
    payload = json.loads((ROOT / "frontend/src/data/dashboard.json").read_text(encoding="utf-8"))

    if "components/dashboard/Dashboard" not in page:
        raise SystemExit("Frontend is missing modular dashboard shell")

    if "PipelineStrip" not in dashboard or "SqlModuleGrid" not in dashboard:
        raise SystemExit("Frontend is missing modular pipeline or SQL sections")

    if "readOrder" not in payload or len(payload["readOrder"]) < 4:
        raise SystemExit("Dashboard payload is missing read order guidance")

    for key in ("healthGuide", "trendGuide", "faultGuide", "agents"):
        if key not in payload:
            raise SystemExit(f"Dashboard payload is missing readability block: {key}")

    if "sessionViews" not in payload or len(payload["sessionViews"]) < 3:
        raise SystemExit("Dashboard payload is missing per-session views")

    if len(payload.get("pipeline", [])) < 5:
        raise SystemExit("Dashboard payload is missing modular pipeline")

    default_view = payload["sessionViews"][str(payload["defaultSessionId"])]
    if len(default_view.get("sqlModules", [])) < 3:
        raise SystemExit("Dashboard payload is missing SQL module cards")

    huginn_steps = [step for step in default_view["agentTrace"] if step["agent"] == "huginn"]
    muninn_steps = [step for step in default_view["agentTrace"] if step["agent"] == "muninn"]
    if len(huginn_steps) < 3 or len(muninn_steps) < 3:
        raise SystemExit("Agent trace is missing Huginn or Muninn steps")

    if not default_view["agentTrace"][0].get("title"):
        raise SystemExit("Agent trace steps are missing plain-language titles")

    records = payload["dataSource"].get("records", [])
    if len(records) < 3:
        raise SystemExit("Provenance records are missing public drive entries")

    resume = (ROOT / "README.md").read_text(encoding="utf-8")
    if "## Resume bullets" not in resume:
        raise SystemExit("README is missing resume bullets section")

    print("Phase 6 polish and readability contract OK")


if __name__ == "__main__":
    main()
