"""Domain exceptions raised by external-service clients."""


class ModelServiceError(RuntimeError):
    """Base exception for model-service client failures."""


class ModelServiceUnavailableError(ModelServiceError):
    """Raised when the model service cannot be reached reliably."""


class ModelServiceResponseError(ModelServiceError):
    """Raised when the model service returns a non-retryable HTTP error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
    ) -> None:
        """Initialize the response error with its HTTP status code."""
        super().__init__(message)
        self.status_code = status_code


class ModelServiceProtocolError(ModelServiceError):
    """Raised when a model-service response violates its contract."""
