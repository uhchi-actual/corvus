from pathlib import Path

from fastapi.testclient import TestClient

from src.main import DISCLAIMER, READ_ONLY_OBD_MODES, app

ROOT = Path(__file__).resolve().parents[2]


def test_health_endpoint_reports_current_contract() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "corvus"
    assert payload["phase"] == "2-sql-core"
    assert payload["status"] == "ok"
    assert payload["read_only_obd_modes"] == list(READ_ONLY_OBD_MODES)
    assert payload["disclaimer"] == DISCLAIMER


def test_no_mode_04_or_write_scope_is_advertised() -> None:
    assert "04" not in READ_ONLY_OBD_MODES
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "Mode 04" in readme
    assert "must not clear diagnostic codes" in security


def test_env_example_keeps_provider_agnostic_llm_contract() -> None:
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

    for key in ("USE_LLM", "LLM_ENDPOINT", "LLM_MODEL", "LLM_API_KEY"):
        assert f"{key}=" in env_example
    assert "JOSIEFIED-Qwen3:8b" in env_example


def test_phase_zero_scaffold_paths_exist() -> None:
    expected_paths = [
        ".github/workflows/ci.yml",
        ".github/workflows/pages.yml",
        "backend/src/ingest",
        "backend/src/sql",
        "backend/src/agent",
        "frontend/src/app",
        "data/schema.sql",
        "data/seed",
        "data/queries",
        "powerbi/screenshots",
        "docs/DOCKER_WSL2_DISK_CAP.md",
    ]

    missing = [path for path in expected_paths if not (ROOT / path).exists()]
    assert missing == []
