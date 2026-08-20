from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


def _load_local_environment() -> Path:
    """Load an explicitly selected env file or the project-local default."""
    override = os.environ.get("ORACULO_ENV_FILE")
    env_path = Path(override).expanduser().resolve() if override else PROJECT_DIR / ".env.local"
    if env_path.is_file():
        load_dotenv(env_path, override=False)
    return env_path


ENV_FILE = _load_local_environment()


def _resolve_data_dir() -> Path:
    configured = os.environ.get("ORACULO_DATA_DIR")
    if not configured:
        return PROJECT_DIR / "data"
    path = Path(configured).expanduser()
    return (PROJECT_DIR / path).resolve() if not path.is_absolute() else path.resolve()


DATA_DIR = _resolve_data_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    app_name: str = "Oráculo"
    api_prefix: str = "/api"
    log_level: str = Field("INFO", validation_alias="ORACULO_LOG_LEVEL")
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{(DATA_DIR / 'oraculo.db').as_posix()}",
        validation_alias="ORACULO_DATABASE_URL",
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        validation_alias="ORACULO_CORS_ORIGINS",
    )

    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    model_critical: str = Field("gpt-5.6-sol", validation_alias="ORACULO_MODEL_CRITICAL")
    model_standard: str = Field("gpt-5.6-terra", validation_alias="ORACULO_MODEL_STANDARD")
    model_light: str = Field("gpt-5.6-luna", validation_alias="ORACULO_MODEL_LIGHT")
    monthly_ai_budget_usd: float = Field(5.0, validation_alias="MONTHLY_AI_BUDGET_USD", ge=0)
    soft_warning_usd: float = Field(4.0, validation_alias="SOFT_WARNING_USD", ge=0)
    hard_limit_usd: float = Field(5.0, validation_alias="HARD_LIMIT_USD", ge=0)
    web_search_enabled: bool = Field(True, validation_alias="ORACULO_WEB_SEARCH_ENABLED")

    scheduler_enabled: bool = Field(True, validation_alias="ORACULO_SCHEDULER_ENABLED")
    timezone: str = Field("UTC", validation_alias="ORACULO_TIMEZONE")
    morning_briefing_time: str = Field("08:00", validation_alias="ORACULO_MORNING_BRIEFING_TIME")
    evening_checkin_time: str = Field("19:00", validation_alias="ORACULO_EVENING_CHECKIN_TIME")
    external_inactivity_days: int = Field(7, validation_alias="ORACULO_EXTERNAL_INACTIVITY_DAYS", ge=1)
    stalled_project_days: int = Field(7, validation_alias="ORACULO_STALLED_PROJECT_DAYS", ge=1)
    backup_retention: int = Field(7, validation_alias="ORACULO_BACKUP_RETENTION", ge=1, le=365)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
