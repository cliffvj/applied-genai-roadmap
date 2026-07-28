"""FastAPI dependencies for shared application resources."""

from typing import cast

from fastapi import Request

from applied_genai.clients.model_service import ModelServiceClient


def get_model_service_client(
    request: Request,
) -> ModelServiceClient:
    """Return the model-service client initialized by application lifespan."""
    client = getattr(
        request.app.state,
        "model_service_client",
        None,
    )

    if client is None:
        raise RuntimeError(
            "The model-service client has not been initialized. "
            "Ensure that the FastAPI lifespan is running.",
        )

    return cast(ModelServiceClient, client)
