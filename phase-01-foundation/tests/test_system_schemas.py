"""Tests for validated system response schemas."""

import pytest
from pydantic import ValidationError

from applied_genai import __version__, project_name
from applied_genai.schemas.system import (
    DependencyReadinessStatus,
    HealthResponse,
    HealthStatus,
    ModelServiceReadiness,
    ReadinessResponse,
    ReadinessStatus,
    ServiceInformation,
    ServiceStatus,
)


def test_service_information_serialization() -> None:
    """Service metadata should serialize to the expected JSON structure."""
    information = ServiceInformation(
        name=project_name(),
        version=__version__,
        status=ServiceStatus.OPERATIONAL,
        documentation="/docs",
    )

    assert information.model_dump(mode="json") == {
        "name": project_name(),
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
    }


def test_service_information_rejects_invalid_version() -> None:
    """A non-semantic version value should fail validation."""
    with pytest.raises(ValidationError):
        ServiceInformation.model_validate(
            {
                "name": project_name(),
                "version": "version-one",
                "status": "operational",
                "documentation": "/docs",
            },
        )


def test_service_information_rejects_unknown_fields() -> None:
    """System schemas should reject undeclared fields."""
    with pytest.raises(ValidationError):
        ServiceInformation.model_validate(
            {
                "name": project_name(),
                "version": __version__,
                "status": "operational",
                "documentation": "/docs",
                "internal_secret": "not-allowed",
            },
        )


def test_health_response_accepts_healthy_state() -> None:
    """The liveness response should accept the healthy state."""
    response = HealthResponse(
        status=HealthStatus.HEALTHY,
    )

    assert response.model_dump(mode="json") == {
        "status": "healthy",
    }


def test_readiness_response_serialization() -> None:
    """Readiness information should serialize to a stable API contract."""
    response = ReadinessResponse(
        status=ReadinessStatus.READY,
        model_service=ModelServiceReadiness(
            required=True,
            status=DependencyReadinessStatus.HEALTHY,
        ),
    )

    assert response.model_dump(mode="json") == {
        "status": "ready",
        "model_service": {
            "required": True,
            "status": "healthy",
        },
    }
