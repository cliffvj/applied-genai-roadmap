"""Asynchronous client for an external model service."""

from collections.abc import Mapping
from typing import Final, TypeVar

import httpx2
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from applied_genai.clients.errors import (
    ModelServiceProtocolError,
    ModelServiceResponseError,
    ModelServiceUnavailableError,
)
from applied_genai.core.config import Settings
from applied_genai.schemas.external import (
    ExternalModelGenerationResponse,
    ExternalServiceHealthResponse,
)
from applied_genai.schemas.prompt import PromptRequest

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset(
    {
        408,
        429,
        500,
        502,
        503,
        504,
    },
)

ResponseSchemaT = TypeVar(
    "ResponseSchemaT",
    bound=BaseModel,
)


class _RetryableStatusError(RuntimeError):
    """Internal exception used to trigger retries for transient HTTP states."""

    def __init__(self, status_code: int) -> None:
        """Store the transient HTTP status code."""
        super().__init__(
            f"External model service returned transient HTTP {status_code}.",
        )
        self.status_code = status_code


class ModelServiceClient:
    """Perform validated asynchronous operations against a model service."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        """Initialize the client from validated application settings."""
        self._settings = settings
        self._owns_http_client = http_client is None

        self._http_client = http_client or httpx2.AsyncClient(
            base_url=settings.model_service_base_url,
            timeout=httpx2.Timeout(
                settings.model_service_timeout_seconds,
            ),
            headers={
                "Accept": "application/json",
                "User-Agent": (f"{settings.app_name}/{settings.app_version}"),
            },
        )

    async def health(self) -> ExternalServiceHealthResponse:
        """Request and validate the model-service health response."""
        response = await self._request_with_retry(
            method="GET",
            path=self._settings.model_service_health_path,
        )

        return self._validate_response(
            response,
            ExternalServiceHealthResponse,
            operation="health check",
        )

    async def generate(
        self,
        request: PromptRequest,
    ) -> ExternalModelGenerationResponse:
        """Submit a prompt and validate the model-service response."""
        response = await self._request_with_retry(
            method="POST",
            path=self._settings.model_service_generate_path,
            json_body=request.model_dump(mode="json"),
        )

        return self._validate_response(
            response,
            ExternalModelGenerationResponse,
            operation="prompt generation",
        )

    async def _request_with_retry(
        self,
        *,
        method: str,
        path: str,
        json_body: Mapping[str, object] | None = None,
    ) -> httpx2.Response:
        """Perform one HTTP operation using the configured retry policy."""
        retrying = AsyncRetrying(
            stop=stop_after_attempt(
                self._settings.model_service_retry_attempts,
            ),
            wait=wait_exponential(
                multiplier=(self._settings.model_service_retry_min_wait_seconds),
                min=self._settings.model_service_retry_min_wait_seconds,
                max=self._settings.model_service_retry_max_wait_seconds,
            ),
            retry=retry_if_exception_type(
                (
                    httpx2.TransportError,
                    _RetryableStatusError,
                ),
            ),
            reraise=True,
        )

        try:
            async for attempt in retrying:
                with attempt:
                    if json_body is None:
                        response = await self._http_client.request(
                            method,
                            path,
                        )
                    else:
                        response = await self._http_client.request(
                            method,
                            path,
                            json=json_body,
                        )

                    if response.status_code in RETRYABLE_STATUS_CODES:
                        raise _RetryableStatusError(
                            response.status_code,
                        )

                    try:
                        response.raise_for_status()
                    except httpx2.HTTPStatusError as exc:
                        raise ModelServiceResponseError(
                            f"External model service returned HTTP {response.status_code}.",
                            status_code=response.status_code,
                        ) from exc

                    return response

        except (
            httpx2.TransportError,
            _RetryableStatusError,
        ) as exc:
            raise ModelServiceUnavailableError(
                "External model service is unavailable after "
                f"{self._settings.model_service_retry_attempts} attempt(s).",
            ) from exc

        raise ModelServiceUnavailableError(
            "External model-service retry processing ended unexpectedly.",
        )

    @staticmethod
    def _validate_response(
        response: httpx2.Response,
        response_schema: type[ResponseSchemaT],
        *,
        operation: str,
    ) -> ResponseSchemaT:
        """Parse and validate an external model-service JSON response."""
        try:
            payload = response.json()
        except ValueError as exc:
            raise ModelServiceProtocolError(
                f"External model service returned invalid JSON during {operation}.",
            ) from exc

        try:
            return response_schema.model_validate(payload)
        except ValidationError as exc:
            raise ModelServiceProtocolError(
                "External model service returned a response that violated "
                f"the {operation} contract.",
            ) from exc

    async def aclose(self) -> None:
        """Close the internally owned HTTP client and its connection pool."""
        if self._owns_http_client:
            await self._http_client.aclose()
