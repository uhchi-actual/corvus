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

    if "HealthMatrix" not in dashboard or "Performance Profile" not in dashboard:
        raise SystemExit("Frontend is missing performance profile chart")

    if "PipelineStrip" in dashboard or "SqlModuleGrid" in dashboard:
        raise SystemExit("Frontend still contains removed pipeline or SQL module sections")

    if "What SQL and the ravens did" in dashboard or "How Corvus fits together" in dashboard:
        raise SystemExit("Frontend still contains removed audit or pipeline copy")

    for key in ("healthGuide", "trendGuide", "faultGuide"):
        if key not in payload:
            raise SystemExit(f"Dashboard payload is missing readability block: {key}")

    if "sessionViews" not in payload or len(payload["sessionViews"]) < 4:
        raise SystemExit("Dashboard payload is missing per-session views")

    default_view = payload["sessionViews"][str(payload["defaultSessionId"])]
    matrix = default_view.get("healthMatrix", [])
    if len(matrix) != 5:
        raise SystemExit("Dashboard payload health matrix must have five axes")

    concerns = default_view.get("performanceConcerns", [])
    if not concerns:
        raise SystemExit("Dashboard payload is missing performance concerns")

    records = payload["dataSource"].get("records", [])
    if len(records) < 4:
        raise SystemExit("Provenance records are missing public drive entries")

    resume = (ROOT / "README.md").read_text(encoding="utf-8")
    if "## Resume bullets" not in resume:
        raise SystemExit("README is missing resume bullets section")

    print("Phase 6 polish and readability contract OK")


if __name__ == "__main__":
    main()
