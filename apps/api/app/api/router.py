from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.imports import router as imports_router
from app.api.routes.templates import router as templates_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(imports_router)
api_router.include_router(templates_router)
