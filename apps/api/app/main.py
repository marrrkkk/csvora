from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from importlib import metadata
from sqlalchemy import text
import redis

from app.api.router import api_router
from app.api.middleware import RequestContextMiddleware
from app.core.config import get_settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from fastapi import HTTPException
from app.db.session import engine
from app.services.storage.factory import build_storage_service


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        app_version = metadata.version("csv-import-fixer-api")
    except Exception:
        app_version = "0.0.0"
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version=app_version,
    )
    app.add_middleware(RequestContextMiddleware)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    def root_health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/health/live", tags=["health"])
    def root_live() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    @app.get("/health/ready", tags=["health"])
    def root_ready():
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

        payload = {"status": "ok" if ready else "degraded", "service": settings.app_name, "checks": checks}
        return JSONResponse(status_code=200 if ready else 503, content=payload)

    return app


app = create_app()
