"""Tests for validated application configuration."""

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from applied_genai import __version__, project_name
from applied_genai.core.config import Settings, get_settings

SETTINGS_ENVIRONMENT_VARIABLES = (
    "APPLIED_GENAI_APP_NAME",
    "APPLIED_GENAI_APP_VERSION",
    "APPLIED_GENAI_ENVIRONMENT",
    "APPLIED_GENAI_DEBUG",
    "APPLIED_GENAI_HOST",
    "APPLIED_GENAI_PORT",
    "APPLIED_GENAI_DOCS_ENABLED",
    "APPLIED_GENAI_LOG_LEVEL",
    "APPLIED_GENAI_MODEL_SERVICE_BASE_URL",
    "APPLIED_GENAI_MODEL_SERVICE_HEALTH_PATH",
    "APPLIED_GENAI_MODEL_SERVICE_GENERATE_PATH",
    "APPLIED_GENAI_MODEL_SERVICE_REQUIRED_FOR_READINESS",
    "APPLIED_GENAI_MODEL_SERVICE_TIMEOUT_SECONDS",
    "APPLIED_GENAI_MODEL_SERVICE_RETRY_ATTEMPTS",
    "APPLIED_GENAI_MODEL_SERVICE_RETRY_MIN_WAIT_SECONDS",
    "APPLIED_GENAI_MODEL_SERVICE_RETRY_MAX_WAIT_SECONDS",
)


class SettingsWithoutDotenv(Settings):
    """Application settings with dotenv loading disabled for tests."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        env_prefix="APPLIED_GENAI_",
        case_sensitive=False,
        extra="ignore",
    )


@pytest.fixture(autouse=True)
def clear_settings_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove application environment variables before every test."""
    for variable_name in SETTINGS_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)


def test_settings_defaults() -> None:
    """Settings should expose safe development defaults."""
    settings = SettingsWithoutDotenv()

    assert settings.app_name == project_name()
    assert settings.app_version == __version__
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.docs_enabled is True
    assert settings.log_level == "INFO"
    assert settings.model_service_base_url == "http://127.0.0.1:8001"
    assert settings.model_service_health_path == "/health"
    assert settings.model_service_generate_path == "/generate"
    assert settings.model_service_timeout_seconds == 10.0
    assert settings.model_service_retry_attempts == 3
    assert settings.model_service_retry_min_wait_seconds == 0.25
    assert settings.model_service_retry_max_wait_seconds == 2.0
    assert settings.model_service_required_for_readiness is True


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables should override default settings."""
    monkeypatch.setenv("APPLIED_GENAI_APP_NAME", "Configured GenAI Service")
    monkeypatch.setenv("APPLIED_GENAI_ENVIRONMENT", "production")
    monkeypatch.setenv("APPLIED_GENAI_DEBUG", "true")
    monkeypatch.setenv("APPLIED_GENAI_PORT", "9000")
    monkeypatch.setenv("APPLIED_GENAI_DOCS_ENABLED", "false")
    monkeypatch.setenv("APPLIED_GENAI_LOG_LEVEL", "WARNING")
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_BASE_URL",
        "https://models.example.com/",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_HEALTH_PATH",
        "/api/health",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_GENERATE_PATH",
        "/api/v1/generate",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_TIMEOUT_SECONDS",
        "30",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_RETRY_ATTEMPTS",
        "4",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_RETRY_MIN_WAIT_SECONDS",
        "0.5",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_RETRY_MAX_WAIT_SECONDS",
        "5",
    )
    monkeypatch.setenv(
        "APPLIED_GENAI_MODEL_SERVICE_REQUIRED_FOR_READINESS",
        "false",
    )

    settings = SettingsWithoutDotenv()

    assert settings.app_name == "Configured GenAI Service"
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.port == 9000
    assert settings.docs_enabled is False
    assert settings.log_level == "WARNING"
    assert settings.model_service_base_url == "https://models.example.com"
    assert settings.model_service_health_path == "/api/health"
    assert settings.model_service_generate_path == "/api/v1/generate"
    assert settings.model_service_timeout_seconds == 30.0
    assert settings.model_service_retry_attempts == 4
    assert settings.model_service_retry_min_wait_seconds == 0.5
    assert settings.model_service_retry_max_wait_seconds == 5.0
    assert settings.model_service_required_for_readiness is False


@pytest.mark.parametrize("invalid_port", [0, 65536])
def test_settings_reject_invalid_ports(invalid_port: int) -> None:
    """Ports outside the valid TCP range should be rejected."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate({"port": invalid_port})


def test_settings_reject_invalid_environment() -> None:
    """Unknown deployment environments should be rejected."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate(
            {"environment": "invalid"},
        )


def test_get_settings_returns_cached_instance() -> None:
    """The settings factory should reuse the same validated object."""
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()


def test_settings_reject_invalid_model_service_url() -> None:
    """The model-service URL should require HTTP or HTTPS."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate(
            {
                "model_service_base_url": "ftp://models.example.com",
            },
        )


def test_settings_reject_invalid_model_service_health_path() -> None:
    """The model-service health path should begin with a slash."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate(
            {
                "model_service_health_path": "health",
            },
        )


def test_settings_reject_invalid_model_service_generate_path() -> None:
    """The model-service generation path should begin with a slash."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate(
            {
                "model_service_generate_path": "generate",
            },
        )


def test_settings_reject_inverted_retry_wait_range() -> None:
    """The maximum retry wait should not be below the minimum."""
    with pytest.raises(ValidationError):
        SettingsWithoutDotenv.model_validate(
            {
                "model_service_retry_min_wait_seconds": 5.0,
                "model_service_retry_max_wait_seconds": 1.0,
            },
        )
