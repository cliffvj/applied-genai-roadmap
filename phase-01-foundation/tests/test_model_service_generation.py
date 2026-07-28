"""Tests for asynchronous model-service prompt generation."""

import asyncio
import json
from collections.abc import Callable

import httpx2
import pytest

from applied_genai.clients.errors import (
    ModelServiceProtocolError,
)
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings
from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
)
from applied_genai.schemas.prompt import PromptRequest

RequestHandler = Callable[[httpx2.Request], httpx2.Response]


def create_generation_settings(
    *,
    retry_attempts: int = 3,
) -> Settings:
    """Create generation settings with retry delays disabled."""
    return Settings(
        environment="test",
        model_service_base_url="https://models.example.com",
        model_service_generate_path="/generate",
        model_service_timeout_seconds=1.0,
        model_service_retry_attempts=retry_attempts,
        model_service_retry_min_wait_seconds=0.0,
        model_service_retry_max_wait_seconds=0.0,
    )


async def run_generation_request(
    handler: RequestHandler,
    *,
    retry_attempts: int = 3,
) -> ExternalModelGenerationResponse:
    """Run one generation operation through a mock transport."""
    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(
        base_url="https://models.example.com",
        transport=transport,
    ) as http_client:
        client = ModelServiceClient(
            create_generation_settings(
                retry_attempts=retry_attempts,
            ),
            http_client=http_client,
        )

        return await client.generate(
            PromptRequest(
                prompt="Explain GPU memory.",
                model_id="qwen2.5:3b",
                temperature=0.2,
                max_tokens=256,
                stop_sequences=["END"],
            ),
        )


def test_model_service_generation_success() -> None:
    """A valid generation result should be parsed and returned."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "POST"
        assert request.url.path == "/generate"

        payload = json.loads(request.content)

        assert payload == {
            "prompt": "Explain GPU memory.",
            "model_id": "qwen2.5:3b",
            "system_prompt": None,
            "temperature": 0.2,
            "max_tokens": 256,
            "stop_sequences": ["END"],
        }

        return httpx2.Response(
            200,
            request=request,
            json={
                "model_id": "qwen2.5:3b",
                "generated_text": ("GPU memory stores model weights and runtime tensors."),
                "prompt_tokens": 4,
                "completion_tokens": 9,
                "finish_reason": "stop",
            },
        )

    result = asyncio.run(
        run_generation_request(handler),
    )

    assert result.model_dump(mode="json") == {
        "model_id": "qwen2.5:3b",
        "generated_text": ("GPU memory stores model weights and runtime tensors."),
        "prompt_tokens": 4,
        "completion_tokens": 9,
        "finish_reason": "stop",
    }


def test_model_service_generation_retries_transient_status() -> None:
    """A transient generation failure should be retried."""
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            return httpx2.Response(
                503,
                request=request,
                json={
                    "detail": "temporarily unavailable",
                },
            )

        return httpx2.Response(
            200,
            request=request,
            json={
                "model_id": "qwen2.5:3b",
                "generated_text": "Generation succeeded.",
                "prompt_tokens": 4,
                "completion_tokens": 3,
                "finish_reason": "stop",
            },
        )

    result = asyncio.run(
        run_generation_request(
            handler,
            retry_attempts=2,
        ),
    )

    assert attempts == 2
    assert result.generated_text == "Generation succeeded."


def test_model_service_generation_rejects_invalid_schema() -> None:
    """An invalid generation response should raise a protocol error."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            request=request,
            json={
                "model_id": "qwen2.5:3b",
                "generated_text": "",
                "prompt_tokens": -1,
                "completion_tokens": 3,
                "finish_reason": "unsupported",
            },
        )

    with pytest.raises(ModelServiceProtocolError):
        asyncio.run(
            run_generation_request(handler),
        )
