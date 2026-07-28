"""Tests for external model-service status routes."""

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


class StubModelServiceClient(ModelServiceClient):
    """Controllable model-service client used by route tests."""

    def __init__(
        self,
        *,
        response: ExternalServiceHealthResponse | None = None,
        error: ModelServiceError | None = None,
    ) -> None:
        """Initialize the stub result or failure."""
        self._response = (
            response
            if response is not None
            else ExternalServiceHealthResponse(
                service="stub-model-service",
                status=ExternalServiceHealthStatus.HEALTHY,
            )
        )
        self._error = error
        self.closed = False

    async def health(self) -> ExternalServiceHealthResponse:
        """Return the configured result or raise the configured error."""
        if self._error is not None:
            raise self._error

        return self._response

    async def aclose(self) -> None:
        """Record application shutdown."""
        self.closed = True


def create_test_application(
    client: StubModelServiceClient,
) -> FastAPI:
    """Create an application using the supplied stub client."""

    def client_factory(
        _settings: Settings,
    ) -> ModelServiceClient:
        return client

    return create_app(
        Settings(environment="test"),
        model_service_client_factory=client_factory,
    )


def test_model_service_status_success() -> None:
    """A healthy upstream service should return HTTP 200."""
    model_service_client = StubModelServiceClient()
    application = create_test_application(
        model_service_client,
    )

    with TestClient(application) as test_client:
        response = test_client.get(
            "/api/v1/model-service/status",
        )

    assert response.status_code == 200
    assert response.json() == {
        "available": True,
        "upstream": {
            "service": "stub-model-service",
            "status": "healthy",
        },
    }
    assert model_service_client.closed is True


def test_model_service_unavailable_returns_503() -> None:
    """An unreachable upstream service should return HTTP 503."""
    application = create_test_application(
        StubModelServiceClient(
            error=ModelServiceUnavailableError(
                "Service unavailable.",
            ),
        ),
    )

    with TestClient(application) as test_client:
        response = test_client.get(
            "/api/v1/model-service/status",
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "External model service is unavailable.",
    }


@pytest.mark.parametrize(
    "error",
    [
        ModelServiceProtocolError(
            "Invalid upstream schema.",
        ),
        ModelServiceResponseError(
            "Upstream returned HTTP 404.",
            status_code=404,
        ),
        ModelServiceError(
            "Unexpected model-service failure.",
        ),
    ],
)
def test_invalid_upstream_response_returns_502(
    error: ModelServiceError,
) -> None:
    """Invalid upstream behavior should return HTTP 502."""
    application = create_test_application(
        StubModelServiceClient(error=error),
    )

    with TestClient(application) as test_client:
        response = test_client.get(
            "/api/v1/model-service/status",
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": ("External model service returned an invalid response."),
    }


def test_model_service_route_is_documented() -> None:
    """OpenAPI should include the model-service status operation."""
    application = create_test_application(
        StubModelServiceClient(),
    )

    with TestClient(application) as test_client:
        response = test_client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert "/api/v1/model-service/status" in schema["paths"]
    assert "ModelServiceStatusResponse" in (schema["components"]["schemas"])
