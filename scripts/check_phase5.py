from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    page = (ROOT / "frontend/src/app/page.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/src/app/globals.css").read_text(encoding="utf-8")
    payload = json.loads((ROOT / "frontend/src/data/dashboard.json").read_text(encoding="utf-8"))

    if "coming soon" in page.lower() or "phase " in page.lower():
        raise SystemExit("Frontend contains placeholder or internal phase copy")

    if "dashboardData" not in page or "agentTrace" not in page:
        raise SystemExit("Frontend is not rendering the static dashboard payload")

    if payload["dataSource"]["license"] != "CC BY 4.0":
        raise SystemExit("Dashboard payload is missing public data license attribution")

    if not payload["agentTraceId"].startswith("agent-") or not payload["agentTrace"]:
        raise SystemExit("Dashboard payload is missing agent trace data")

    agents = {step["agent"] for step in payload["agentTrace"]}
    if not {"huginn", "muninn", "corvus"} <= agents:
        raise SystemExit(f"Dashboard trace is missing expected agents: {sorted(agents)}")

    if "directional" not in payload["focus"]["score_basis"]:
        raise SystemExit("Health score is not labeled as directional")

    inspiration_path = ROOT / "frontend/public" / payload["inspiration"]["image"]
    if not inspiration_path.exists():
        raise SystemExit(f"Missing inspiration asset: {inspiration_path}")

    if "prefers-reduced-motion" not in styles or "flow-in" not in styles:
        raise SystemExit("Dashboard motion contract is incomplete")

    print("Phase 5 static dashboard contract OK")


if __name__ == "__main__":
    main()
