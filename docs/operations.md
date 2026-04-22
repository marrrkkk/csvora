# Operations Runbook

## Purpose

Run and operate the CSV Import Fixer API locally or in a Docker-based environment with predictable startup, health checks, and shutdown.

## Startup Order

1. Create env file:
   - `cp .env.example .env`
2. Start dependencies and services:
   - `make dev`
3. Apply database migrations:
   - `make migrate`
4. Confirm service health:
   - `curl http://localhost:8000/health/live`
   - `curl http://localhost:8000/health/ready`
5. Confirm metrics endpoint:
   - `curl http://localhost:8000/api/v1/metrics`

Compose equivalents remain valid:
- `docker compose up -d --build`
- `docker compose run --rm api alembic upgrade head`

## Operational Smoke Checks

- Liveness:
  - `GET /health/live` returns `200`
- Readiness:
  - `GET /health/ready` returns `200` and dependency checks as `ok`
- API readiness equivalent:
  - `GET /api/v1/health/ready`
- Metrics exposure:
  - `GET /api/v1/metrics` returns Prometheus text format

## Migration Flow

- Apply latest migrations:
  - `make migrate`
- Check current migration revision:
  - `docker compose run --rm api alembic current`
- Inspect migration history:
  - `docker compose run --rm api alembic history`

## Basic API Smoke Flow

1. Create import
2. Upload CSV
3. Trigger analyze
4. Poll status until `analyzed`
5. Trigger transform
6. Poll status until `completed`
7. Fetch result payload and artifact keys

All import endpoints require `X-API-Key`.

## Shutdown

- Stop all services:
  - `make down`
- Stop and remove volumes (destructive local reset):
  - `docker compose down -v`

## Notes

- Status transitions are monotonic:
  - `created -> uploaded -> analyzing -> analyzed -> transforming -> completed|failed`
- Duplicate analyze/transform triggers return `409` and should not enqueue duplicate work.
