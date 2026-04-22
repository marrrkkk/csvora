# Rate limits

Protected routes use Redis-backed rate limiting.

## Expected behavior

- When enabled, responses include `X-RateLimit-*` headers.
- If Redis is unavailable and fail-open is enabled, requests continue with degraded limiter behavior.

## Configuration

See the config reference in the backend repo:

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_PER_MINUTE`
- `RATE_LIMIT_GLOBAL_PER_MINUTE`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_FAIL_OPEN`
- `RATE_LIMIT_REDIS_TIMEOUT_MS`

