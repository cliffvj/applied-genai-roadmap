"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from applied_genai import __version__, project_name

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Validated runtime settings for the Applied GenAI service."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="APPLIED_GENAI_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default_factory=project_name,
        min_length=1,
        max_length=100,
        description="Human-readable application name.",
    )
    app_version: str = Field(
        default=__version__,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Application version using semantic version format.",
    )
    environment: Literal[
        "development",
        "test",
        "staging",
        "production",
    ] = "development"
    debug: bool = False
    host: str = Field(
        default="127.0.0.1",
        min_length=1,
        description="Network interface on which the API listens.",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="TCP port on which the API listens.",
    )
    docs_enabled: bool = True
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Create and cache the application settings."""
    return Settings()
