"""Validated schemas for service information and health endpoints."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from applied_genai.schemas.base import ApiSchema

ServiceName = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=100,
    ),
]

SemanticVersion = Annotated[
    str,
    StringConstraints(
        pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$",
    ),
]

DocumentationPath = Annotated[
    str,
    StringConstraints(
        min_length=1,
        pattern=r"^/",
    ),
]

RuntimeEnvironment = Literal[
    "development",
    "test",
    "staging",
    "production",
]


class ServiceStatus(StrEnum):
    """Supported service operational states."""

    OPERATIONAL = "operational"


class HealthStatus(StrEnum):
    """Supported application health states."""

    HEALTHY = "healthy"


class ReadinessStatus(StrEnum):
    """Supported application readiness states."""

    READY = "ready"
    NOT_READY = "not_ready"


class DependencyReadinessStatus(StrEnum):
    """Supported readiness states for an external dependency."""

    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"
    NOT_REQUIRED = "not_required"


class ModelServiceReadiness(ApiSchema):
    """Readiness information for the external model service."""

    required: bool = Field(
        description=(
            "Whether external model-service availability is required for application readiness."
        ),
    )
    status: DependencyReadinessStatus = Field(
        description="Current readiness state of the model-service dependency.",
    )


class ReadinessResponse(ApiSchema):
    """Response returned by the application readiness probe."""

    status: ReadinessStatus = Field(
        description="Current readiness state of the API.",
    )
    model_service: ModelServiceReadiness = Field(
        description="Readiness state of the external model-service dependency.",
    )


class ServiceInformation(ApiSchema):
    """Public metadata for the running API service."""

    name: ServiceName = Field(
        description="Human-readable service name.",
        examples=["Applied GenAI Foundation"],
    )
    version: SemanticVersion = Field(
        description="Service version using semantic version format.",
        examples=["0.1.0"],
    )
    status: ServiceStatus = Field(
        description="Current operational status of the service.",
    )
    documentation: DocumentationPath | None = Field(
        description=(
            "Relative path to interactive API documentation, "
            "or null when documentation is disabled."
        ),
        examples=["/docs"],
    )


class HealthResponse(ApiSchema):
    """Response returned by the liveness probe."""

    status: HealthStatus = Field(
        description="Current application health state.",
    )


class ApiStatusResponse(ApiSchema):
    """Operational information for a versioned API."""

    api_version: Literal["v1"] = Field(
        description="Public API contract version.",
    )
    service: ServiceName = Field(
        description="Human-readable service name.",
    )
    version: SemanticVersion = Field(
        description="Running application version.",
    )
    status: ServiceStatus = Field(
        description="Current operational status.",
    )
    environment: RuntimeEnvironment = Field(
        description="Current application deployment environment.",
    )
    debug: bool = Field(
        description="Whether FastAPI debug behavior is enabled.",
    )
    documentation_enabled: bool = Field(
        description="Whether OpenAPI and interactive documentation are enabled.",
    )
