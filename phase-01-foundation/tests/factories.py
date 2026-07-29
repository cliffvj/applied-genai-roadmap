"""Deterministic factories shared across the Phase 1 test suite."""

from pydantic_settings import SettingsConfigDict

from applied_genai.core.config import Settings
from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
    ExternalServiceHealthResponse,
    ExternalServiceHealthStatus,
)
from applied_genai.schemas.prompt import (
    GenerationFinishReason,
    PromptRequest,
)


class SettingsWithoutExternalSources(Settings):
    """Settings variant that does not read a dotenv file."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_prefix="APPLIED_GENAI_",
        case_sensitive=False,
        extra="ignore",
    )


DEFAULT_TEST_SETTINGS: dict[str, object] = {
    "app_name": "Applied GenAI Foundation Test",
    "app_version": "0.1.0",
    "environment": "test",
    "debug": False,
    "host": "127.0.0.1",
    "port": 8000,
    "docs_enabled": True,
    "log_level": "INFO",
    "model_service_base_url": "https://models.example.com",
    "model_service_health_path": "/health",
    "model_service_generate_path": "/generate",
    "model_service_required_for_readiness": False,
    "model_service_timeout_seconds": 1.0,
    "model_service_retry_attempts": 3,
    "model_service_retry_min_wait_seconds": 0.0,
    "model_service_retry_max_wait_seconds": 0.0,
}

DEFAULT_PROMPT_PAYLOAD: dict[str, object] = {
    "prompt": "Explain GPU memory allocation.",
    "model_id": "qwen2.5:3b",
    "system_prompt": None,
    "temperature": 0.2,
    "max_tokens": 256,
    "stop_sequences": [],
}


def create_test_settings(
    **overrides: object,
) -> Settings:
    """Create settings without consulting dotenv or external sources."""
    values = DEFAULT_TEST_SETTINGS.copy()
    values.update(overrides)

    return SettingsWithoutExternalSources.model_validate(values)


def create_prompt_payload(
    **overrides: object,
) -> dict[str, object]:
    """Create a valid prompt dictionary with optional overrides."""
    payload = DEFAULT_PROMPT_PAYLOAD.copy()
    payload.update(overrides)

    return payload


def create_prompt_request(
    **overrides: object,
) -> PromptRequest:
    """Create a validated prompt request."""
    return PromptRequest.model_validate(
        create_prompt_payload(**overrides),
    )


def create_health_response() -> ExternalServiceHealthResponse:
    """Create a deterministic healthy upstream response."""
    return ExternalServiceHealthResponse(
        service="test-model-service",
        status=ExternalServiceHealthStatus.HEALTHY,
    )


def create_generation_response() -> ExternalModelGenerationResponse:
    """Create a deterministic upstream generation response."""
    return ExternalModelGenerationResponse(
        model_id="qwen2.5:3b",
        generated_text="GPU memory stores model weights and runtime tensors.",
        prompt_tokens=5,
        completion_tokens=8,
        finish_reason=GenerationFinishReason.STOP,
    )
