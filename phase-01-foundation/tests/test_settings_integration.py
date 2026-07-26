"""Tests for FastAPI settings dependency integration."""

from fastapi.testclient import TestClient

from applied_genai.core.config import Settings, get_settings
from applied_genai.main import create_app


def test_settings_dependency_can_be_overridden() -> None:
    """FastAPI should support replacing settings for an application test."""
    application = create_app()

    override_settings = Settings(
        app_name="Dependency Override Service",
        app_version="2.0.0",
        environment="staging",
        debug=False,
        docs_enabled=True,
    )

    def get_override_settings() -> Settings:
        return override_settings

    application.dependency_overrides[get_settings] = get_override_settings

    test_client = TestClient(application)
    response = test_client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v1",
        "service": "Dependency Override Service",
        "version": "2.0.0",
        "status": "operational",
        "environment": "staging",
        "debug": False,
        "documentation_enabled": True,
    }
