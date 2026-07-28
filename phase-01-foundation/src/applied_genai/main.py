"""FastAPI application entry point."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from applied_genai.api.router import api_router
from applied_genai.clients.model_service import ModelServiceClient
from applied_genai.core.config import Settings, get_settings

ModelServiceClientFactory = Callable[
    [Settings],
    ModelServiceClient,
]


def create_app(
    settings: Settings | None = None,
    *,
    model_service_client_factory: ModelServiceClientFactory | None = None,
) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    resolved_settings = settings if settings is not None else get_settings()

    if model_service_client_factory is None:
        client_factory: ModelServiceClientFactory = ModelServiceClient
    else:
        client_factory = model_service_client_factory

    @asynccontextmanager
    async def lifespan(
        fastapi_app: FastAPI,
    ) -> AsyncIterator[None]:
        """Create and release resources shared across application requests."""
        model_service_client = client_factory(resolved_settings)
        fastapi_app.state.model_service_client = model_service_client

        try:
            yield
        finally:
            await model_service_client.aclose()

    openapi_url = "/openapi.json" if resolved_settings.docs_enabled else None
    docs_url = "/docs" if resolved_settings.docs_enabled else None
    redoc_url = "/redoc" if resolved_settings.docs_enabled else None

    application = FastAPI(
        title=resolved_settings.app_name,
        summary="Foundation API for the Applied GenAI engineering roadmap.",
        description=(
            "A production-oriented API foundation that will be extended with "
            "LLM inference, retrieval, GPU infrastructure, and AI platform capabilities."
        ),
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
        contact={
            "name": "Clifford V. Juan",
        },
        license_info={
            "name": "MIT",
        },
    )

    def application_settings() -> Settings:
        """Return the settings bound to this application instance."""
        return resolved_settings

    application.dependency_overrides[get_settings] = application_settings
    application.include_router(api_router)

    return application


app: FastAPI = create_app()
