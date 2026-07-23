"""System information and health-check endpoints."""

from typing import Literal, TypedDict

from fastapi import APIRouter, status

from applied_genai import __version__, project_name

router = APIRouter(tags=["System"])


class ServiceInformation(TypedDict):
    """Response structure for service information."""

    name: str
    version: str
    status: Literal["operational"]
    documentation: str


class HealthResponse(TypedDict):
    """Response structure for service health checks."""

    status: Literal["healthy", "ready"]


class ApiStatusResponse(TypedDict):
    """Response structure for the versioned API status endpoint."""

    api_version: Literal["v1"]
    service: str
    version: str
    status: Literal["operational"]


@router.get(
    "/",
    response_model=ServiceInformation,
    summary="Get service information",
    description="Return basic metadata and operational status for the API service.",
)
async def service_information() -> ServiceInformation:
    """Return service name, version, status, and documentation location."""
    return {
        "name": project_name(),
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
    }


@router.get(
    "/health/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application liveness",
    description="Confirm that the API process is running and can handle requests.",
)
async def liveness() -> HealthResponse:
    """Return a successful response while the application process is alive."""
    return {"status": "healthy"}


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check application readiness",
    description="Confirm that the API is ready to receive application traffic.",
)
async def readiness() -> HealthResponse:
    """Return a successful response while the application is ready."""
    return {"status": "ready"}


@router.get(
    "/api/v1/status",
    response_model=ApiStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get versioned API status",
    description="Return operational information for version 1 of the API.",
)
async def api_status() -> ApiStatusResponse:
    """Return the status and version of the versioned API."""
    return {
        "api_version": "v1",
        "service": project_name(),
        "version": __version__,
        "status": "operational",
    }
