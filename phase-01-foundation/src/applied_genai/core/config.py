"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
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

    model_service_base_url: str = Field(
        default="http://127.0.0.1:8001",
        min_length=1,
        max_length=2048,
        pattern=r"^https?://",
        description="Base URL of the external model service.",
    )
    model_service_health_path: str = Field(
        default="/health",
        min_length=1,
        max_length=255,
        pattern=r"^/",
        description="Relative health-check path exposed by the model service.",
    )
    model_service_generate_path: str = Field(
        default="/generate",
        min_length=1,
        max_length=255,
        pattern=r"^/",
        description="Relative prompt-generation path exposed by the model service.",
    )
    model_service_required_for_readiness: bool = Field(
        default=True,
        description=(
            "Whether model-service availability is required before the API "
            "is considered ready to receive traffic."
        ),
    )
    model_service_timeout_seconds: float = Field(
        default=10.0,
        gt=0.0,
        le=120.0,
        description="Maximum duration of an external HTTP operation.",
    )
    model_service_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of attempts for transient failures.",
    )
    model_service_retry_min_wait_seconds: float = Field(
        default=0.25,
        ge=0.0,
        le=10.0,
        description="Minimum retry-backoff duration.",
    )
    model_service_retry_max_wait_seconds: float = Field(
        default=2.0,
        ge=0.0,
        le=30.0,
        description="Maximum retry-backoff duration.",
    )

    @field_validator("model_service_base_url")
    @classmethod
    def normalize_model_service_base_url(cls, value: str) -> str:
        """Remove trailing slashes from the configured base URL."""
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_retry_wait_range(self) -> Self:
        """Ensure the maximum retry wait is not below the minimum."""
        if self.model_service_retry_max_wait_seconds < self.model_service_retry_min_wait_seconds:
            raise ValueError(
                "model_service_retry_max_wait_seconds must be greater than "
                "or equal to model_service_retry_min_wait_seconds.",
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Create and cache the application settings."""
    return Settings()
