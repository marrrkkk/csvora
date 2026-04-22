# csvora

Production-ready CSV import fixing service: versioned templates describe arbitrary schemas, and transforms normalize and validate rows from template metadata.  
csvora ingests messy CSV files, analyzes structure and mappings, transforms data into a canonical schema, validates rows, and outputs cleaned artifacts.

## Monorepo Layout

- `apps/api`: FastAPI backend, Celery worker, Alembic migrations, tests
- `docs`: operator runbooks
- `scripts`: root utility scripts
- `docker-compose.yml`: root local orchestration

## Runbook Index

- Operations: [`docs/operations.md`](docs/operations.md)
- Deploy and rollback: [`docs/deploy-and-rollback.md`](docs/deploy-and-rollback.md)
- Incident triage: [`docs/incident-triage.md`](docs/incident-triage.md)
- Config reference: [`docs/config-reference.md`](docs/config-reference.md)
- Agent/operator rules: [`AGENTS.md`](AGENTS.md)

## Core Capabilities

- Define **import templates** (versioned field definitions, aliases, thresholds, optional AI assist)
- Create imports (optionally bound to a template) and upload CSV files
- Analyze encoding, delimiter, header row, and **template-scored** mapping suggestions with review/auto-accept behavior
- Approve mappings when review is required, then transform using finalized mappings only
- Transform and normalize data using each template version’s field types, normalizers, and validation rules (legacy non-template imports still use the built-in contact column set)
- Validate data and return row-level warnings/errors
- Store and expose output references:
  - cleaned CSV
  - normalized JSON
  - validation report

## Canonical Contacts Schema

- `first_name`
- `last_name`
- `full_name`
- `email`
- `phone`
- `company`
- `job_title`
- `city`
- `state`
- `country`
- `tags`
- `notes`

## API Endpoints

### Templates
- `POST /api/v1/templates`
- `GET /api/v1/templates`
- `GET /api/v1/templates/{id}`
- `PATCH /api/v1/templates/{id}`
- `POST /api/v1/templates/{id}/archive`
- `POST /api/v1/templates/{id}/versions`

### Imports
- `POST /api/v1/imports` (optional `template_id` pins the latest active template version at creation)
- `GET /api/v1/imports/{id}`
- `POST /api/v1/imports/{id}/upload`
- `POST /api/v1/imports/{id}/analyze`
- `GET /api/v1/imports/{id}/status`
- `GET /api/v1/imports/{id}/analysis`
- `POST /api/v1/imports/{id}/approve-mappings` (when status is `needs_review`)
- `POST /api/v1/imports/{id}/transform` (for template auto-accept flows, call with `{}` once status is `ready_to_transform`)
- `GET /api/v1/imports/{id}/result`

### Health and Metrics
- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/metrics`

## Local Run

### Prerequisites

- Docker Desktop (with Compose)
- `make` (optional convenience wrapper; direct `docker compose` commands still supported)

Windows note: if `make` is not installed, use the PowerShell helpers:

- `./scripts/dev.ps1`
- `./scripts/migrate.ps1`
- `./scripts/test.ps1`
- `./scripts/web.ps1`
- `./scripts/docs-sync.ps1`

### Root Commands

- `make dev`: start full local stack (`api`, `worker`, `postgres`, `redis`) with build.
- `make api`: start API service.
- `make worker`: start worker service.
- `make migrate`: apply Alembic migrations.
- `make test`: apply migrations and run the backend test suite (`alembic upgrade head && pytest`). Rebuild the API image after code changes: `docker compose build api`.
- `make down`: stop stack.
- `make web`: run the web app (Next.js dev server) from `apps/web`.
- `make docs-sync`: export/sync OpenAPI spec into `apps/web/public/openapi.json`.

### Run the web app (without make)

```bash
npm --prefix apps/web run dev
```

### Sync OpenAPI spec for web API reference

From the repo root:

```bash
make docs-sync
```

Without make:

```bash
py -3 scripts/openapi_sync.py
```

### Start

```bash
cp .env.example .env
make dev
make migrate
```

### Smoke checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/v1/metrics
```

## Authentication and Rate Limiting

- All `/api/v1/imports/*` endpoints require `X-API-Key`.
- API keys are DB-backed and validated using bcrypt hashes.
- Key lifecycle controls include:
  - `is_active`
  - `revoked_at`
  - `expires_at`
- Redis-backed rate limiting applies on protected routes and emits rate-limit headers.
- When Redis limiter is unavailable and fail-open is enabled, requests continue with degraded limiter policy.

### Create local API key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```bash
RAW_KEY="<RAW_KEY>" docker compose run --rm api python -c "from app.core.security import hash_api_key, build_key_prefix; import os; raw=os.environ['RAW_KEY']; print(build_key_prefix(raw)); print(hash_api_key(raw))"
```

```bash
docker compose exec -T postgres psql -U csv_import_fixer -d csv_import_fixer -c "insert into api_keys (id, key_prefix, key_hash, name, is_active) values ('<UUID>', '<KEY_PREFIX>', '<KEY_HASH>', 'local-dev', true);"
```

## Data Safety Behavior Notes

- Transform mapping requests are strictly validated:
  - no duplicate `source_column`
  - no duplicate `target_field`
  - canonical target fields only
- Missing mapped source columns generate explicit issues.
- Fully empty normalized rows are skipped and logged as warnings.
- Phone validation warnings can be upgraded to errors via `TRANSFORM_PHONE_WARNING_IS_ERROR`.

## Testing

```bash
make dev
make migrate
make test
```

Direct compose equivalent:

```bash
docker compose up -d --build
docker compose run --rm api alembic upgrade head
docker compose run --rm -e TEST_BASE_URL=http://api:8000 api pytest -q
```

## Releases

Semantic versioning is managed in `apps/api/pyproject.toml`.

```bash
python scripts/version.py patch --dry-run
python scripts/version.py patch --git
```

Release flow:
1. Bump version
2. Run full tests
3. Commit release
4. Tag release
5. Push commit and tags

## Documentation Maintenance Rule

When runtime behavior, commands, or endpoint contracts change:
- update this `README.md`,
- update relevant `docs/*.md` runbook,
- re-run and verify documented commands.
