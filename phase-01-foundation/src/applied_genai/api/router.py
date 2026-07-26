"""Central API router configuration."""

from fastapi import APIRouter

from applied_genai.api.routes.prompts import router as prompts_router
from applied_genai.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(prompts_router)
