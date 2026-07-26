"""Prompt validation endpoints."""

from fastapi import APIRouter, status

from applied_genai.schemas.prompt import (
    PromptRequest,
    PromptValidationResponse,
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
        "Validate and normalize a future language-model request without performing model inference."
    ),
)
async def validate_prompt(
    request: PromptRequest,
) -> PromptValidationResponse:
    """Return the normalized request after successful validation."""
    return PromptValidationResponse(request=request)
