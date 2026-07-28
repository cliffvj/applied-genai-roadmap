"""External model-service API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from applied_genai.api.dependencies import get_model_service_client
from applied_genai.clients.errors import (
    ModelServiceError,
    ModelServiceProtocolError,
    ModelServiceResponseError,
    ModelServiceUnavailableError,
)
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.schemas.external import ModelServiceStatusResponse

router = APIRouter(
    prefix="/api/v1/model-service",
    tags=["Model Service"],
)


@router.get(
    "/status",
    response_model=ModelServiceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check external model-service status",
    description=(
        "Contact the configured external model service and return its validated health status."
    ),
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "The upstream service returned an invalid response.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The upstream service could not be reached reliably.",
        },
    },
)
async def model_service_status(
    client: Annotated[
        ModelServiceClient,
        Depends(get_model_service_client),
    ],
) -> ModelServiceStatusResponse:
    """Return validated availability information for the model service."""
    try:
        upstream_health = await client.health()
    except ModelServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External model service is unavailable.",
        ) from exc
    except (
        ModelServiceProtocolError,
        ModelServiceResponseError,
        ModelServiceError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External model service returned an invalid response.",
        ) from exc

    return ModelServiceStatusResponse(
        upstream=upstream_health,
    )
