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

    settings = SettingsWithoutDotenv()

    assert settings.app_name == "Configured GenAI Service"
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.port == 9000
    assert settings.docs_enabled is False
    assert settings.log_level == "WARNING"


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
