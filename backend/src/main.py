from fastapi import FastAPI

from .config import get_settings

PROJECT_SLUG = "corvus"
PHASE = "0-scaffold"
DISCLAIMER = (
    "Directional diagnostic guidance based on logged data - not a substitute for "
    "inspection by a certified technician."
)
READ_ONLY_OBD_MODES = ("01", "02", "03", "07", "09")


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

    return app


app = create_app()

