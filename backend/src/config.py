from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_llm: bool = True
    llm_endpoint: str = "http://localhost:11434/v1"
    llm_model: str = "JOSIEFIED-Qwen3:8b"
    llm_api_key: str = "not-needed-for-local"
    database_url: str = "sqlite:///data/seed/corvus.db"
    obd_port: str = "auto"


@lru_cache
def get_settings() -> Settings:
    return Settings()

