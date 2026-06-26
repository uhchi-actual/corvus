from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    page = (ROOT / "frontend/src/app/page.tsx").read_text(encoding="utf-8")
    payload = json.loads((ROOT / "frontend/src/data/dashboard.json").read_text(encoding="utf-8"))

    if "agents.huginn" not in page or "agents.muninn" not in page:
        raise SystemExit("Frontend is missing Huginn and Muninn sections")

    if "readOrder" not in payload or len(payload["readOrder"]) < 4:
        raise SystemExit("Dashboard payload is missing read order guidance")

    for key in ("healthGuide", "trendGuide", "faultGuide", "agents"):
        if key not in payload:
            raise SystemExit(f"Dashboard payload is missing readability block: {key}")

    huginn_steps = [step for step in payload["agentTrace"] if step["agent"] == "huginn"]
    muninn_steps = [step for step in payload["agentTrace"] if step["agent"] == "muninn"]
    if len(huginn_steps) < 3 or len(muninn_steps) < 3:
        raise SystemExit("Agent trace is missing Huginn or Muninn steps")

    if not payload["agentTrace"][0].get("title"):
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
