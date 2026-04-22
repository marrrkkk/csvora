import types

import pytest
from fastapi import HTTPException, Request
import redis

from app.core.rate_limit import enforce_rate_limit
from app.core.config import Settings


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, ttl: int) -> None:
        return None


def test_rate_limit_raises_429_when_exceeded(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr("app.core.rate_limit._redis_client", lambda settings: fake)

    scope = {"type": "http", "method": "POST", "path": "/api/v1/imports", "headers": []}
    request = Request(scope)
    request._url = types.SimpleNamespace(path="/api/v1/imports")  # type: ignore[attr-defined]
    request._client = types.SimpleNamespace(host="127.0.0.1")  # type: ignore[attr-defined]
    request.state.api_key_id = "k1"

    settings = Settings(rate_limit_enabled=True, rate_limit_per_minute=1, rate_limit_global_per_minute=10)

    headers = enforce_rate_limit(request, settings)
    assert "X-RateLimit-Limit" in headers
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(request, settings)
    assert getattr(exc.value, "status_code", None) == 429
    assert exc.value.headers is not None
    assert "Retry-After" in exc.value.headers


def test_rate_limit_global_bucket_enforced(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr("app.core.rate_limit._redis_client", lambda settings: fake)

    scope = {"type": "http", "method": "GET", "path": "/api/v1/imports/abc", "headers": []}
    request = Request(scope)
    request._url = types.SimpleNamespace(path="/api/v1/imports/abc")  # type: ignore[attr-defined]
    request._client = types.SimpleNamespace(host="127.0.0.1")  # type: ignore[attr-defined]
    request.state.api_key_id = "k1"

    settings = Settings(rate_limit_enabled=True, rate_limit_per_minute=10, rate_limit_global_per_minute=1)
    enforce_rate_limit(request, settings)
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(request, settings)
    assert exc.value.status_code == 429


def test_rate_limit_fail_open_on_redis_error(monkeypatch) -> None:
    class _BrokenRedis:
        def incr(self, key: str) -> int:
            raise redis.RedisError("redis down")

    monkeypatch.setattr("app.core.rate_limit._redis_client", lambda settings: _BrokenRedis())
    scope = {"type": "http", "method": "GET", "path": "/api/v1/imports", "headers": []}
    request = Request(scope)
    request._url = types.SimpleNamespace(path="/api/v1/imports")  # type: ignore[attr-defined]
    request._client = types.SimpleNamespace(host="127.0.0.1")  # type: ignore[attr-defined]

    settings = Settings(rate_limit_enabled=True, rate_limit_fail_open=True)
    headers = enforce_rate_limit(request, settings)
    assert headers.get("X-RateLimit-Policy") == "degraded"

