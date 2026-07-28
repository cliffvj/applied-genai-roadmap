"""Tests for the asynchronous external model-service client."""

import asyncio
from collections.abc import Callable

import httpx2
import pytest

from applied_genai.clients.errors import (
    ModelServiceProtocolError,
    ModelServiceResponseError,
    ModelServiceUnavailableError,
)
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings
from applied_genai.schemas.external import ExternalServiceHealthResponse

RequestHandler = Callable[[httpx2.Request], httpx2.Response]


def create_test_settings(
    *,
    retry_attempts: int = 3,
) -> Settings:
    """Create model-service settings with retry delays disabled."""
    return Settings(
        environment="test",
        model_service_base_url="https://models.example.com",
        model_service_timeout_seconds=1.0,
        model_service_retry_attempts=retry_attempts,
        model_service_retry_min_wait_seconds=0.0,
        model_service_retry_max_wait_seconds=0.0,
    )


async def run_health_request(
    handler: RequestHandler,
    *,
    retry_attempts: int = 3,
) -> ExternalServiceHealthResponse:
    """Run one health operation through an HTTPX2 mock transport."""
    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(
        base_url="https://models.example.com",
        transport=transport,
    ) as http_client:
        client = ModelServiceClient(
            create_test_settings(
                retry_attempts=retry_attempts,
            ),
            http_client=http_client,
        )

        return await client.health()


def test_model_service_health_success() -> None:
    """A valid upstream health response should be returned as a schema."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/health"

        return httpx2.Response(
            200,
            request=request,
            json={
                "service": "mock-model-service",
                "status": "healthy",
            },
        )

    result = asyncio.run(run_health_request(handler))

    assert result.model_dump(mode="json") == {
        "service": "mock-model-service",
        "status": "healthy",
    }


def test_model_service_retries_transient_status() -> None:
    """Transient HTTP failures should be retried before succeeding."""
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1

        if attempts < 3:
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
                "service": "mock-model-service",
                "status": "healthy",
            },
        )

    result = asyncio.run(
        run_health_request(
            handler,
            retry_attempts=3,
        ),
    )

    assert attempts == 3
    assert result.status.value == "healthy"


def test_model_service_raises_unavailable_after_retries() -> None:
    """Exhausted transient responses should raise an availability error."""
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1

        return httpx2.Response(
            503,
            request=request,
            json={
                "detail": "temporarily unavailable",
            },
        )

    with pytest.raises(ModelServiceUnavailableError):
        asyncio.run(
            run_health_request(
                handler,
                retry_attempts=3,
            ),
        )

    assert attempts == 3


def test_model_service_does_not_retry_non_transient_status() -> None:
    """A non-transient client error should fail without retrying."""
    attempts = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1

        return httpx2.Response(
            404,
            request=request,
            json={
                "detail": "not found",
            },
        )

    with pytest.raises(ModelServiceResponseError) as error:
        asyncio.run(run_health_request(handler))

    assert error.value.status_code == 404
    assert attempts == 1


def test_model_service_rejects_invalid_json() -> None:
    """Malformed JSON should raise a protocol error."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            request=request,
            content=b"not-json",
            headers={
                "content-type": "application/json",
            },
        )

    with pytest.raises(ModelServiceProtocolError):
        asyncio.run(run_health_request(handler))


def test_model_service_rejects_invalid_response_schema() -> None:
    """A response violating the expected schema should be rejected."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            request=request,
            json={
                "service": "mock-model-service",
                "status": "unknown",
            },
        )

    with pytest.raises(ModelServiceProtocolError):
        asyncio.run(run_health_request(handler))
