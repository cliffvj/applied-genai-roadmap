"""Tests for model-service client lifespan management."""

from fastapi.testclient import TestClient

from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings
from applied_genai.main import create_app
from applied_genai.schemas.external import (
    ExternalServiceHealthResponse,
    ExternalServiceHealthStatus,
)


class TrackingModelServiceClient(ModelServiceClient):
    """Test client that records health calls and shutdown."""

    def __init__(self) -> None:
        """Initialize lifecycle tracking state."""
        self.health_calls = 0
        self.closed = False

    async def health(self) -> ExternalServiceHealthResponse:
        """Return a deterministic healthy response."""
        self.health_calls += 1

        return ExternalServiceHealthResponse(
            service="tracking-model-service",
            status=ExternalServiceHealthStatus.HEALTHY,
        )

    async def aclose(self) -> None:
        """Record that application shutdown released the client."""
        self.closed = True


def test_lifespan_creates_and_closes_model_service_client() -> None:
    """Application lifespan should acquire and release one shared client."""
    created_clients: list[TrackingModelServiceClient] = []

    def client_factory(
        _settings: Settings,
    ) -> ModelServiceClient:
        client = TrackingModelServiceClient()
        created_clients.append(client)
        return client

    application = create_app(
        Settings(environment="test"),
        model_service_client_factory=client_factory,
    )

    assert created_clients == []

    with TestClient(application) as test_client:
        assert len(created_clients) == 1
        assert application.state.model_service_client is created_clients[0]

        response = test_client.get(
            "/api/v1/model-service/status",
        )

        assert response.status_code == 200
        assert created_clients[0].health_calls == 1
        assert created_clients[0].closed is False

    assert created_clients[0].closed is True
