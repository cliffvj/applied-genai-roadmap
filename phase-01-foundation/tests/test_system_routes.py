"""Tests for service information and lightweight system routes."""

from fastapi.testclient import TestClient

from applied_genai import __version__, project_name
from applied_genai.main import app

client = TestClient(app)


def test_service_information() -> None:
    """The root endpoint should return configured service information."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": project_name(),
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
    }


def test_liveness() -> None:
    """Liveness should report that the running process is healthy."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_api_v1_status() -> None:
    """The versioned status endpoint should report runtime metadata."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v1",
        "service": project_name(),
        "version": __version__,
        "status": "operational",
        "environment": "development",
        "debug": False,
        "documentation_enabled": True,
    }


def test_unknown_route_returns_not_found() -> None:
    """An undefined route should return HTTP 404."""
    response = client.get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Not Found",
    }
