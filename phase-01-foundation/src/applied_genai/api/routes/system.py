"""System information and health-check endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from applied_genai.api.dependencies import get_model_service_client
from applied_genai.clients.errors import ModelServiceError
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings, get_settings
from applied_genai.schemas.system import (
    ApiStatusResponse,
    DependencyReadinessStatus,
    HealthResponse,
    HealthStatus,
    ModelServiceReadiness,
    ReadinessResponse,
    ReadinessStatus,
    ServiceInformation,
    ServiceStatus,
)

router = APIRouter(tags=["System"])


@router.get(
    "/",
    response_model=ServiceInformation,
    summary="Get service information",
    description="Return basic metadata and operational status for the API service.",
)
async def service_information(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ServiceInformation:
    """Return service name, version, status, and documentation location."""
    documentation = "/docs" if settings.docs_enabled else None

    return ServiceInformation(
        name=settings.app_name,
        version=settings.app_version,
        status=ServiceStatus.OPERATIONAL,
        documentation=documentation,
    )


@router.get(
    "/health/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application liveness",
    description="Confirm that the API process is running and can handle requests.",
)
async def liveness() -> HealthResponse:
    """Return a successful response while the application process is alive."""
    return HealthResponse(
        status=HealthStatus.HEALTHY,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application readiness",
    description=(
        "Confirm that the API and its required external dependencies are ready to receive traffic."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": ("The API is running but a required dependency is unavailable."),
        },
    },
)
async def readiness(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[
        ModelServiceClient,
        Depends(get_model_service_client),
    ],
) -> ReadinessResponse:
    """Return readiness based on required external dependencies."""
    if not settings.model_service_required_for_readiness:
        return ReadinessResponse(
            status=ReadinessStatus.READY,
            model_service=ModelServiceReadiness(
                required=False,
                status=DependencyReadinessStatus.NOT_REQUIRED,
            ),
        )

    try:
        await client.health()
    except ModelServiceError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status=ReadinessStatus.NOT_READY,
            model_service=ModelServiceReadiness(
                required=True,
                status=DependencyReadinessStatus.UNAVAILABLE,
            ),
        )

    return ReadinessResponse(
        status=ReadinessStatus.READY,
        model_service=ModelServiceReadiness(
            required=True,
            status=DependencyReadinessStatus.HEALTHY,
        ),
    )


@router.get(
    "/api/v1/status",
    response_model=ApiStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get versioned API status",
    description="Return operational information for version 1 of the API.",
)
async def api_status(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApiStatusResponse:
    """Return the status and runtime configuration of the versioned API."""
    return ApiStatusResponse(
        api_version="v1",
        service=settings.app_name,
        version=settings.app_version,
        status=ServiceStatus.OPERATIONAL,
        environment=settings.environment,
        debug=settings.debug,
        documentation_enabled=settings.docs_enabled,
    )
