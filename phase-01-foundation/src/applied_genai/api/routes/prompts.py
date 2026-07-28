"""Prompt validation and generation endpoints."""

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
from applied_genai.schemas.prompt import (
    PromptGenerationResponse,
    PromptRequest,
    PromptValidationResponse,
    TokenUsage,
)

router = APIRouter(
    prefix="/api/v1/prompts",
    tags=["Prompts"],
)


@router.post(
    "/validate",
    response_model=PromptValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a GenAI prompt request",
    description=(
        "Validate and normalize a language-model request without performing model inference."
    ),
)
async def validate_prompt(
    request: PromptRequest,
) -> PromptValidationResponse:
    """Return the normalized request after successful validation."""
    return PromptValidationResponse(request=request)


@router.post(
    "/generate",
    response_model=PromptGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a model response",
    description=(
        "Submit a validated prompt to the configured external model "
        "service and return its validated generation result."
    ),
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "The model service returned an invalid response.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The model service could not be reached reliably.",
        },
    },
)
async def generate_prompt(
    request: PromptRequest,
    client: Annotated[
        ModelServiceClient,
        Depends(get_model_service_client),
    ],
) -> PromptGenerationResponse:
    """Generate a response through the external model service."""
    try:
        result = await client.generate(request)
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

    return PromptGenerationResponse(
        model_id=result.model_id,
        generated_text=result.generated_text,
        finish_reason=result.finish_reason,
        usage=TokenUsage(
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=(result.prompt_tokens + result.completion_tokens),
        ),
    )
