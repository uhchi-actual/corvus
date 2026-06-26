from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.agent import LlmConfig, analyze_session  # noqa: E402
from src.main import DISCLAIMER  # noqa: E402

DB_PATH = ROOT / "data" / "seed" / "corvus.db"
QUERY_DIR = ROOT / "data" / "queries"
CONFIG_PATH = ROOT / "data" / "health_score_config.json"


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(DB_PATH)],
        check=True,
    )

    result = analyze_session(
        session_id=1,
        database_path=DB_PATH,
        query_dir=QUERY_DIR,
        config_path=CONFIG_PATH,
        disclaimer=DISCLAIMER,
        llm_config=LlmConfig(enabled=False, endpoint="", model="", api_key=""),
    )

    if result["status"] != "ok":
        raise SystemExit(f"Phase 3 graph failed: {result.get('error')}")
    if result["disclaimer"] != DISCLAIMER:
        raise SystemExit("Phase 3 graph response is missing the mandatory disclaimer")
    if not result["agent_trace_id"] or not result["agent_trace"]:
        raise SystemExit("Phase 3 graph response is missing agent trace data")
    if not result["findings"] or result["findings"][0]["agent_trace_id"] != result["agent_trace_id"]:
        raise SystemExit("Phase 3 report writer did not return a traced finding")
    agents = {step["agent"] for step in result["agent_trace"]}
    if not {"huginn", "muninn", "corvus"}.issubset(agents):
        raise SystemExit(f"Phase 3 trace is missing expected agents: {sorted(agents)}")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--database", str(DB_PATH)],
        check=True,
    )
    print("Phase 3 agent contract OK")


if __name__ == "__main__":
    main()
