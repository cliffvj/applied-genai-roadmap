"""Tests for service information and health-check routes."""

from fastapi.testclient import TestClient

from applied_genai import __version__, project_name
from applied_genai.main import app

client = TestClient(app)


def test_service_information() -> None:
    """The root endpoint should return service information."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": project_name(),
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
    }


def test_liveness() -> None:
    """The liveness endpoint should report a healthy process."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness() -> None:
    """The readiness endpoint should report that the API is ready."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_api_v1_status() -> None:
    """The versioned status endpoint should report API metadata."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v1",
        "service": project_name(),
        "version": __version__,
        "status": "operational",
    }


def test_unknown_route_returns_not_found() -> None:
    """An undefined route should return HTTP 404."""
    response = client.get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
