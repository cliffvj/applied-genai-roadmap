"""FastAPI application entry point."""

from fastapi import FastAPI

from applied_genai import __version__, project_name
from applied_genai.api.router import api_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=project_name(),
        summary="Foundation API for the Applied GenAI engineering roadmap.",
        description=(
            "A production-oriented API foundation that will be extended with "
            "LLM inference, retrieval, GPU infrastructure, and AI platform capabilities."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Clifford V. Juan",
        },
        license_info={
            "name": "MIT",
        },
    )

    application.include_router(api_router)

    return application


app = create_app()
