"""Tests for dependency-aware application readiness."""

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
    ExternalServiceHealthResponse,
    ExternalServiceHealthStatus,
)


class ReadinessModelServiceClient(ModelServiceClient):
    """Controllable model-service client for readiness tests."""

    def __init__(
        self,
        *,
        error: ModelServiceError | None = None,
    ) -> None:
        """Initialize the configured upstream behavior."""
        self._error = error
        self.health_calls = 0
        self.closed = False

    async def health(self) -> ExternalServiceHealthResponse:
        """Return a healthy response or raise the configured failure."""
        self.health_calls += 1

        if self._error is not None:
            raise self._error

        return ExternalServiceHealthResponse(
            service="readiness-model-service",
            status=ExternalServiceHealthStatus.HEALTHY,
        )

    async def aclose(self) -> None:
        """Record that application shutdown released the client."""
        self.closed = True


def create_readiness_application(
    client: ReadinessModelServiceClient,
    *,
    required: bool = True,
) -> FastAPI:
    """Create an application using controlled readiness dependencies."""

    def client_factory(
        _settings: Settings,
    ) -> ModelServiceClient:
        return client

    return create_app(
        Settings(
            environment="test",
            model_service_required_for_readiness=required,
        ),
        model_service_client_factory=client_factory,
    )


def test_readiness_succeeds_when_model_service_is_healthy() -> None:
    """A healthy required model service should produce HTTP 200."""
    model_service_client = ReadinessModelServiceClient()
    application = create_readiness_application(
        model_service_client,
    )

    with TestClient(application) as test_client:
        response = test_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "model_service": {
            "required": True,
            "status": "healthy",
        },
    }
    assert model_service_client.health_calls == 1
    assert model_service_client.closed is True


@pytest.mark.parametrize(
    "error",
    [
        ModelServiceUnavailableError(
            "Model service is unavailable.",
        ),
        ModelServiceProtocolError(
            "Model service returned an invalid response.",
        ),
        ModelServiceResponseError(
            "Model service returned HTTP 404.",
            status_code=404,
        ),
        ModelServiceError(
            "Unexpected model-service failure.",
        ),
    ],
)
def test_readiness_fails_when_required_model_service_fails(
    error: ModelServiceError,
) -> None:
    """Any required model-service failure should produce HTTP 503."""
    model_service_client = ReadinessModelServiceClient(
        error=error,
    )
    application = create_readiness_application(
        model_service_client,
    )

    with TestClient(application) as test_client:
        response = test_client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "model_service": {
            "required": True,
            "status": "unavailable",
        },
    }
    assert model_service_client.health_calls == 1


def test_readiness_skips_optional_model_service() -> None:
    """An optional model service should not block application readiness."""
    model_service_client = ReadinessModelServiceClient(
        error=ModelServiceUnavailableError(
            "The optional service is unavailable.",
        ),
    )
    application = create_readiness_application(
        model_service_client,
        required=False,
    )

    with TestClient(application) as test_client:
        response = test_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "model_service": {
            "required": False,
            "status": "not_required",
        },
    }
    assert model_service_client.health_calls == 0


def test_liveness_does_not_contact_model_service() -> None:
    """Liveness should remain independent from external dependencies."""
    model_service_client = ReadinessModelServiceClient(
        error=ModelServiceUnavailableError(
            "Model service is unavailable.",
        ),
    )
    application = create_readiness_application(
        model_service_client,
    )

    with TestClient(application) as test_client:
        response = test_client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }
    assert model_service_client.health_calls == 0


def test_readiness_responses_are_documented() -> None:
    """OpenAPI should document successful and failed readiness responses."""
    application = create_readiness_application(
        ReadinessModelServiceClient(),
    )

    with TestClient(application) as test_client:
        response = test_client.get("/openapi.json")

    assert response.status_code == 200

    operation = response.json()["paths"]["/health/ready"]["get"]
    responses = operation["responses"]

    assert "200" in responses
    assert "503" in responses
    assert "ReadinessResponse" in (response.json()["components"]["schemas"])
