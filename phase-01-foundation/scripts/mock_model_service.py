"""Local mock model service for manual async-client testing."""

from fastapi import FastAPI

from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
    ExternalServiceHealthResponse,
    ExternalServiceHealthStatus,
)
from applied_genai.schemas.prompt import (
    GenerationFinishReason,
    PromptRequest,
)

app = FastAPI(
    title="Applied GenAI Mock Model Service",
    version="0.1.0",
)


@app.get(
    "/health",
    response_model=ExternalServiceHealthResponse,
)
async def health() -> ExternalServiceHealthResponse:
    """Return a deterministic healthy service response."""
    return ExternalServiceHealthResponse(
        service="local-mock-model-service",
        status=ExternalServiceHealthStatus.HEALTHY,
    )


@app.post(
    "/generate",
    response_model=ExternalModelGenerationResponse,
)
async def generate(
    request: PromptRequest,
) -> ExternalModelGenerationResponse:
    """Return a deterministic response for the submitted prompt."""
    generated_text = f"Mock model response for: {request.prompt}"

    return ExternalModelGenerationResponse(
        model_id=request.model_id,
        generated_text=generated_text,
        prompt_tokens=len(request.prompt.split()),
        completion_tokens=len(generated_text.split()),
        finish_reason=GenerationFinishReason.STOP,
    )
