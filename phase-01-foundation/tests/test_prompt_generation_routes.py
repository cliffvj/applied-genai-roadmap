"""Tests for asynchronous prompt-generation routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from applied_genai.clients.errors import (
    ModelServiceError,
    ModelServiceProtocolError,
    ModelServiceResponseError,
    ModelServiceUnavailableError,
)
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings
from applied_genai.main import create_app
from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
)
from applied_genai.schemas.prompt import (
    GenerationFinishReason,
    PromptRequest,
)


class StubGenerationClient(ModelServiceClient):
    """Controllable model-service client for generation-route tests."""

    def __init__(
        self,
        *,
        response: ExternalModelGenerationResponse | None = None,
        error: ModelServiceError | None = None,
    ) -> None:
        """Initialize the configured generation behavior."""
        self._response = response or ExternalModelGenerationResponse(
            model_id="qwen2.5:3b",
            generated_text="GPU memory stores model weights.",
            prompt_tokens=5,
            completion_tokens=6,
            finish_reason=GenerationFinishReason.STOP,
        )
        self._error = error
        self.closed = False

    async def generate(
        self,
        _request: PromptRequest,
    ) -> ExternalModelGenerationResponse:
        """Return the configured response or raise the configured error."""
        if self._error is not None:
            raise self._error

        return self._response

    async def aclose(self) -> None:
        """Record application shutdown."""
        self.closed = True


def create_generation_application(
    client: StubGenerationClient,
) -> FastAPI:
    """Create an application using the supplied generation client."""

    def client_factory(
        _settings: Settings,
    ) -> ModelServiceClient:
        return client

    return create_app(
        Settings(
            environment="test",
            model_service_required_for_readiness=False,
        ),
        model_service_client_factory=client_factory,
    )


def test_prompt_generation_success() -> None:
    """A valid prompt should return the generated text and usage."""
    model_service_client = StubGenerationClient()
    application = create_generation_application(
        model_service_client,
    )

    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/v1/prompts/generate",
            json={
                "prompt": "Explain GPU memory.",
                "model_id": "qwen2.5:3b",
                "max_tokens": 256,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "model_id": "qwen2.5:3b",
        "generated_text": "GPU memory stores model weights.",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 6,
            "total_tokens": 11,
        },
    }
    assert model_service_client.closed is True


def test_prompt_generation_rejects_invalid_request() -> None:
    """Invalid prompt input should return HTTP 422 before upstream use."""
    application = create_generation_application(
        StubGenerationClient(),
    )

    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/v1/prompts/generate",
            json={
                "prompt": "   ",
                "temperature": 5.0,
            },
        )

    assert response.status_code == 422


def test_prompt_generation_unavailable_returns_503() -> None:
    """An unavailable model service should produce HTTP 503."""
    application = create_generation_application(
        StubGenerationClient(
            error=ModelServiceUnavailableError(
                "Model service unavailable.",
            ),
        ),
    )

    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/v1/prompts/generate",
            json={
                "prompt": "Explain GPU memory.",
            },
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "External model service is unavailable.",
    }


@pytest.mark.parametrize(
    "error",
    [
        ModelServiceProtocolError(
            "Invalid generation response.",
        ),
        ModelServiceResponseError(
            "Model service returned HTTP 400.",
            status_code=400,
        ),
        ModelServiceError(
            "Unexpected model-service failure.",
        ),
    ],
)
def test_prompt_generation_invalid_upstream_returns_502(
    error: ModelServiceError,
) -> None:
    """Invalid upstream behavior should produce HTTP 502."""
    application = create_generation_application(
        StubGenerationClient(error=error),
    )

    with TestClient(application) as test_client:
        response = test_client.post(
            "/api/v1/prompts/generate",
            json={
                "prompt": "Explain GPU memory.",
            },
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": ("External model service returned an invalid response."),
    }


def test_prompt_generation_route_is_documented() -> None:
    """OpenAPI should include the prompt-generation operation."""
    application = create_generation_application(
        StubGenerationClient(),
    )

    with TestClient(application) as test_client:
        response = test_client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert "/api/v1/prompts/generate" in schema["paths"]
    assert "PromptGenerationResponse" in (schema["components"]["schemas"])
