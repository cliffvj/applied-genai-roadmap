"""Tests for external model-service response schemas."""

import pytest
from pydantic import ValidationError

from applied_genai.schemas.external import (
    ExternalServiceHealthResponse,
    ExternalServiceHealthStatus,
    ModelServiceStatusResponse,
)


def test_external_service_health_response() -> None:
    """A valid external health response should serialize normally."""
    response = ExternalServiceHealthResponse(
        service="mock-model-service",
        status=ExternalServiceHealthStatus.HEALTHY,
    )

    assert response.model_dump(mode="json") == {
        "service": "mock-model-service",
        "status": "healthy",
    }


def test_external_service_health_normalizes_service_name() -> None:
    """The external service name should be stripped."""
    response = ExternalServiceHealthResponse.model_validate(
        {
            "service": "  mock-model-service  ",
            "status": "healthy",
        },
    )

    assert response.service == "mock-model-service"


def test_external_service_health_rejects_unknown_status() -> None:
    """An unsupported health state should fail validation."""
    with pytest.raises(ValidationError):
        ExternalServiceHealthResponse.model_validate(
            {
                "service": "mock-model-service",
                "status": "degraded",
            },
        )


def test_external_service_health_rejects_unknown_fields() -> None:
    """External contracts should reject undeclared response fields."""
    with pytest.raises(ValidationError):
        ExternalServiceHealthResponse.model_validate(
            {
                "service": "mock-model-service",
                "status": "healthy",
                "secret": "not-allowed",
            },
        )


def test_model_service_status_response() -> None:
    """The API wrapper should serialize validated upstream health."""
    response = ModelServiceStatusResponse(
        upstream=ExternalServiceHealthResponse(
            service="mock-model-service",
            status=ExternalServiceHealthStatus.HEALTHY,
        ),
    )

    assert response.model_dump(mode="json") == {
        "available": True,
        "upstream": {
            "service": "mock-model-service",
            "status": "healthy",
        },
    }
