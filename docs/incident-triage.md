# Incident Triage Playbook

## Fast Triage Order

1. Check liveness:
   - `curl http://localhost:8000/health/live`
2. Check readiness:
   - `curl http://localhost:8000/health/ready`
3. Check metrics:
   - `curl http://localhost:8000/api/v1/metrics`
4. Check container status/logs:
   - `docker compose ps`
   - `docker compose logs --tail=200 api worker redis postgres`

## Symptom: 429 Storms

Expected observations:
- high rate of `429 Too Many Requests`
- `X-RateLimit-*` headers present on protected routes

Actions:
1. Confirm request burst is expected (load test vs production traffic).
2. Review rate-limit env values:
   - `RATE_LIMIT_ENABLED`
   - `RATE_LIMIT_PER_MINUTE`
   - `RATE_LIMIT_GLOBAL_PER_MINUTE`
   - `RATE_LIMIT_WINDOW_SECONDS`
3. Check Redis connectivity/latency.
4. If Redis is degraded and fail-open is `false`, expect increased rejections.

## Symptom: Worker Jobs Stuck in Analyzing/Transforming

Expected observations:
- import status remains `analyzing` or `transforming` too long
- no transition to `analyzed/completed/failed`

Actions:
1. Check worker process is up:
   - `docker compose ps worker`
2. Inspect worker logs:
   - `docker compose logs --tail=200 worker`
3. Verify Redis broker is reachable.
4. Re-check duplicate trigger handling (`409` indicates already in progress).
5. If task crashed repeatedly, inspect retry/backoff events and root exception.

## Symptom: Readiness Failing

Expected observations:
- `/health/live` is `200`
- `/health/ready` is `503`
- payload indicates failing dependency (`db`, `redis`, or `storage`)

Actions:
1. Use readiness payload to identify dependency.
2. Validate service container is healthy (`postgres`, `redis`).
3. Validate configured storage root or S3 credentials.
4. Re-run readiness after fixing dependency.

## Symptom: Transform Failures or Unexpected Invalid Rows

Expected observations:
- import transitions to `failed`
- result/issue payload includes row-level errors/warnings

Actions:
1. Confirm mappings use valid canonical fields only.
2. Check for duplicate mapping targets/sources in request payload.
3. Validate source CSV contains mapped headers.
4. Inspect issue severities:
   - phone warnings may be promoted to errors with `TRANSFORM_PHONE_WARNING_IS_ERROR=true`.
5. For malformed CSVs, verify analyzer warning/error output before retriggering.

## Symptom: Auth Failures

Expected observations:
- `401` for missing key
- `403` for invalid/revoked/expired key

Actions:
1. Verify `X-API-Key` header is present.
2. Confirm key row is active and not revoked.
3. Confirm `expires_at` is in the future.
4. Confirm stored `key_prefix` and `key_hash` match the raw key.
