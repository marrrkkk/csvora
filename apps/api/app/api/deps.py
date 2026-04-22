from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.core.security import authenticate_api_key, touch_api_key_usage
from app.db.session import get_db_session
from app.models.api_key import APIKey
from app.services.storage.base import StorageService
from app.services.storage.factory import build_storage_service


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_storage_service() -> StorageService:
    settings = get_settings()
    return build_storage_service(settings)


def require_api_key(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> APIKey:
    settings = get_settings()
    if not settings.auth_enabled:
        request.state.api_key_id = None
        return APIKey(key_hash="", name="disabled", is_active=True)  # type: ignore[arg-type]

    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key")

    api_key = authenticate_api_key(db, x_api_key)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    touch_api_key_usage(db, api_key)
    request.state.api_key_id = str(api_key.id)
    request.state.api_key_name = api_key.name
    return api_key


def rate_limit_guard(request: Request, response: Response) -> None:
    settings = get_settings()
    headers = enforce_rate_limit(request, settings)
    for key, value in headers.items():
        response.headers[key] = value


def require_api_key_and_rate_limit(
    request: Request,
    response: Response,
    api_key: APIKey = Depends(require_api_key),
) -> APIKey:
    settings = get_settings()
    headers = enforce_rate_limit(request, settings)
    for key, value in headers.items():
        response.headers[key] = value
    return api_key
