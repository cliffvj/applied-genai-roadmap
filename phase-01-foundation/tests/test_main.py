"""Tests for FastAPI application construction and metadata."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from applied_genai import __version__, project_name
from applied_genai.main import app, create_app

client = TestClient(app)


def test_create_app_returns_fastapi_application() -> None:
    """The application factory should return a FastAPI instance."""
    application = create_app()

    assert isinstance(application, FastAPI)


def test_application_metadata() -> None:
    """The application should expose the expected project metadata."""
    assert app.title == project_name()
    assert app.version == __version__
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
