from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.agent import LlmConfig, analyze_session
from src.config import get_settings
from src.main import DISCLAIMER, app
from tests.helpers import CONFIG_PATH, QUERY_DIR, connect, seeded_db

ROOT = Path(__file__).resolve().parents[2]


def test_huginn_muninn_graph_returns_trace_and_sql_facts(tmp_path: Path) -> None:
    db_path = seeded_db(tmp_path)

    result = analyze_session(
        session_id=1,
        database_path=db_path,
        query_dir=QUERY_DIR,
        config_path=CONFIG_PATH,
        disclaimer=DISCLAIMER,
        llm_config=LlmConfig(enabled=False, endpoint="", model="", api_key=""),
    )

    assert result["status"] == "ok"
    assert result["disclaimer"] == DISCLAIMER
    assert result["agent_trace_id"].startswith("agent-")
    assert {step["agent"] for step in result["agent_trace"]} >= {"huginn", "muninn", "corvus"}
    assert "baseline_deviation" in result["sql_facts"]
    assert "session_health_score" in result["sql_facts"]
    assert result["findings"][0]["agent_trace_id"] == result["agent_trace_id"]

    with connect(db_path) as conn:
        stored_trace = conn.execute(
            "SELECT agent_trace_id FROM findings WHERE finding_id = ?",
            (result["findings"][0]["finding_id"],),
        ).fetchone()[0]
    assert stored_trace == result["agent_trace_id"]


def test_agent_error_path_keeps_disclaimer_and_trace(tmp_path: Path) -> None:
    db_path = seeded_db(tmp_path)

    result = analyze_session(
        session_id=999,
        database_path=db_path,
        query_dir=QUERY_DIR,
        config_path=CONFIG_PATH,
        disclaimer=DISCLAIMER,
        llm_config=LlmConfig(enabled=False, endpoint="", model="", api_key=""),
    )

    assert result["status"] == "error"
    assert result["disclaimer"] == DISCLAIMER
    assert result["agent_trace_id"].startswith("agent-")
    assert result["agent_trace"][-1]["node"] == "error"
    assert "Session not found" in result["error"]


def test_analysis_endpoint_uses_provider_agnostic_llm_toggle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = seeded_db(tmp_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        response = client.post("/analysis/session/1?use_llm=false")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["disclaimer"] == DISCLAIMER
    assert payload["agent_trace_id"].startswith("agent-")
    assert payload["findings"][0]["agent_trace_id"] == payload["agent_trace_id"]


def test_analysis_endpoint_config_error_keeps_disclaimer_and_trace(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/corvus")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        response = client.post("/analysis/session/1?use_llm=false")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    payload = response.json()
    assert payload["disclaimer"] == DISCLAIMER
    assert payload["agent_trace_id"].startswith("agent-")
    assert payload["agent_trace"][0]["node"] == "configuration"
