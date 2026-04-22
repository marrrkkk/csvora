import time

import redis
from fastapi import HTTPException, Request, status

from app.core.config import Settings


def _redis_client(settings: Settings) -> redis.Redis:
    timeout = max(settings.rate_limit_redis_timeout_ms, 1) / 1000
    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
    )


def _principal(request: Request) -> str:
    api_key_id = getattr(request.state, "api_key_id", None) or "anonymous"
    client_ip = request.client.host if request.client else "unknown"
    return str(api_key_id) if api_key_id != "anonymous" else client_ip


def _increment_with_ttl(client: redis.Redis, key: str, ttl_seconds: int) -> int:
    count = client.incr(key)
    if count == 1:
        client.expire(key, ttl_seconds)
    return count


def enforce_rate_limit(request: Request, settings: Settings) -> dict[str, str]:
    if not settings.rate_limit_enabled:
        return {}

    window = max(settings.rate_limit_window_seconds, 1)
    bucket = int(time.time() // window)
    now = int(time.time())
    reset_epoch = (bucket + 1) * window
    remaining_seconds = max(reset_epoch - now, 1)

    principal = _principal(request)
    route_key = f"rl:route:{principal}:{request.method}:{request.url.path}:{bucket}"
    global_key = f"rl:global:{principal}:{bucket}"

    try:
        client = _redis_client(settings)
        route_count = _increment_with_ttl(client, route_key, window + 10)
        global_count = _increment_with_ttl(client, global_key, window + 10)
    except redis.RedisError:
        if settings.rate_limit_fail_open:
            return {"X-RateLimit-Policy": "degraded"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter unavailable",
        )

    route_limit = max(settings.rate_limit_per_minute, 1)
    global_limit = max(settings.rate_limit_global_per_minute, 1)
    effective_limit = min(route_limit, global_limit)
    remaining = max(min(route_limit - route_count, global_limit - global_count), 0)

    headers = {
        "X-RateLimit-Limit": str(effective_limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_epoch),
    }

    if route_count > route_limit or global_count > global_limit:
        headers["Retry-After"] = str(remaining_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=headers,
        )
    return headers
