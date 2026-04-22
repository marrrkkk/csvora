import json
from collections.abc import Mapping, Sequence

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, Sequence):
        return [_jsonable(v) for v in value]
    return str(value)


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": exc.detail,
                "request_id": _request_id(request),
            }
        },
        headers=getattr(exc, "headers", None),
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = json.dumps(
        {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": str(exc),
                "request_id": _request_id(request),
            }
        },
        default=str,
    )
    return Response(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        media_type="application/json",
        content=body,
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "request_id": _request_id(request),
            }
        },
    )
