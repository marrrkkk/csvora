from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
import redis

from app.core.config import get_settings
from app.core.metrics import render_prometheus
from app.db.session import engine
from app.services.storage.factory import build_storage_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/health/live")
def live_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/health/ready")
def ready_check():
    settings = get_settings()
    checks: dict[str, str] = {"database": "ok", "redis": "ok", "storage": "ok"}
    ready = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"
        ready = False

    try:
        timeout = max(settings.readiness_redis_timeout_ms, 1) / 1000
        redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            decode_responses=True,
        ).ping()
    except Exception:
        checks["redis"] = "error"
        ready = False

    try:
        storage = build_storage_service(settings)
        storage.get_object_reference("healthcheck")
    except Exception:
        checks["storage"] = "error"
        ready = False

    payload = {
        "status": "ok" if ready else "degraded",
        "service": settings.app_name,
        "environment": settings.app_env,
        "checks": checks,
    }
    return JSONResponse(status_code=200 if ready else 503, content=payload)


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    return render_prometheus()
