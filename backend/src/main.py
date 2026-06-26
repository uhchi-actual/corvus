from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .agent import LlmConfig, analyze_session
from .config import get_settings

PROJECT_SLUG = "corvus"
PHASE = "3-agent"
DISCLAIMER = (
    "Directional diagnostic guidance based on logged data - not a substitute for "
    "inspection by a certified technician."
)
READ_ONLY_OBD_MODES = ("01", "02", "03", "07", "09")
ROOT = Path(__file__).resolve().parents[2]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Corvus API",
        version="0.1.0",
        summary="Read-only OBD-II diagnostic analysis scaffold.",
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        settings = get_settings()
        return {
            "project": PROJECT_SLUG,
            "phase": PHASE,
            "status": "ok",
            "read_only_obd_modes": READ_ONLY_OBD_MODES,
            "llm_enabled": settings.use_llm,
            "llm_model": settings.llm_model,
            "database_url": settings.database_url,
            "disclaimer": DISCLAIMER,
        }

    @app.post("/analysis/session/{session_id}")
    def session_analysis(session_id: int, use_llm: bool | None = None) -> JSONResponse:
        settings = get_settings()
        try:
            database_path = _sqlite_path(settings.database_url)
        except ValueError as exc:
            trace_id = f"agent-{uuid4().hex}"
            return JSONResponse(
                {
                    "status": "error",
                    "session_id": session_id,
                    "disclaimer": DISCLAIMER,
                    "agent_trace_id": trace_id,
                    "agent_trace": [
                        {
                            "agent": "corvus",
                            "node": "configuration",
                            "kind": "deterministic",
                            "summary": (
                                "Analysis stopped because database configuration is invalid."
                            ),
                        }
                    ],
                    "sql_facts": {},
                    "dtc_summary": None,
                    "correlation_summary": None,
                    "recommendations": [],
                    "findings": [],
                    "error": str(exc),
                },
                status_code=400,
            )
        result = analyze_session(
            session_id=session_id,
            database_path=database_path,
            query_dir=ROOT / "data" / "queries",
            config_path=ROOT / "data" / "health_score_config.json",
            disclaimer=DISCLAIMER,
            llm_config=LlmConfig(
                enabled=settings.use_llm if use_llm is None else use_llm,
                endpoint=settings.llm_endpoint,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
            ),
        )
        status_code = 200 if result["status"] == "ok" else 404
        return JSONResponse(result, status_code=status_code)

    return app


def _sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Corvus currently expects a sqlite:/// DATABASE_URL")
    raw_path = database_url.removeprefix(prefix)
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return ROOT / path


app = create_app()
