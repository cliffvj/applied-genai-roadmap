"""Tests for FastAPI application construction and metadata."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from applied_genai import __version__, project_name
from applied_genai.core.config import Settings
from applied_genai.main import app, create_app

client = TestClient(app)


def test_create_app_returns_fastapi_application() -> None:
    """The application factory should return a FastAPI instance."""
    application = create_app()

    assert isinstance(application, FastAPI)


def test_application_metadata() -> None:
    """The application should expose the expected default metadata."""
    assert app.title == project_name()
    assert app.version == __version__
    assert app.debug is False
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_openapi_schema_is_available() -> None:
    """The OpenAPI schema should describe the API and its current version."""
    response = client.get("/openapi.json")

    assert response.status_code == 200

    payload = response.json()

    assert payload["info"]["title"] == project_name()
    assert payload["info"]["version"] == __version__


def test_swagger_documentation_is_available() -> None:
    """Swagger UI should be available at the configured documentation path."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_redoc_documentation_is_available() -> None:
    """ReDoc should be available at the configured documentation path."""
    response = client.get("/redoc")

    assert response.status_code == 200
    assert "redoc" in response.text.lower()


def test_create_app_uses_supplied_settings() -> None:
    """The factory should apply a supplied settings object consistently."""
    settings = Settings(
        app_name="Configured GenAI Service",
        app_version="1.2.3",
        environment="test",
        debug=True,
        docs_enabled=False,
    )

    application = create_app(settings)
    configured_client = TestClient(application)

    assert application.title == "Configured GenAI Service"
    assert application.version == "1.2.3"
    assert application.debug is True
    assert application.docs_url is None
    assert application.redoc_url is None
    assert application.openapi_url is None

    service_response = configured_client.get("/")

    assert service_response.status_code == 200
    assert service_response.json() == {
        "name": "Configured GenAI Service",
        "version": "1.2.3",
        "status": "operational",
        "documentation": None,
    }

    status_response = configured_client.get("/api/v1/status")

    assert status_response.status_code == 200
    assert status_response.json() == {
        "api_version": "v1",
        "service": "Configured GenAI Service",
        "version": "1.2.3",
        "status": "operational",
        "environment": "test",
        "debug": True,
        "documentation_enabled": False,
    }


def test_disabled_documentation_routes_return_not_found() -> None:
    """Documentation routes should not exist when documentation is disabled."""
    settings = Settings(
        environment="test",
        docs_enabled=False,
    )

    application = create_app(settings)
    configured_client = TestClient(application)

    assert configured_client.get("/docs").status_code == 404
    assert configured_client.get("/redoc").status_code == 404
    assert configured_client.get("/openapi.json").status_code == 404
