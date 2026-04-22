# AGENTS.md

## Mission

Build and maintain csvora: a production-minded CSV import fixer API for structured CSV data (developer-defined schemas) with clean architecture, predictable behavior, and strong local developer ergonomics.

## Operator Documentation

- Primary entrypoint: `README.md`
- Operations runbook: `docs/operations.md`
- Deploy/rollback runbook: `docs/deploy-and-rollback.md`
- Incident playbooks: `docs/incident-triage.md`
- Config/env reference: `docs/config-reference.md`

## Product Scope (Do Not Expand Without Request)

- Schema-driven imports: templates carry a `schema_type` label (for example `contacts`, `products`) and versioned fields with types, normalizers, and validation rules
- Optional starter JSON for a contacts-shaped version lives in [`apps/api/app/services/template_presets.py`](apps/api/app/services/template_presets.py); it is documentation-style seed data only (not enforced by the server)
- Metrics: `csvora_events_total` includes `analyze_completed` (labels: `template_id`, `template_version_id`, `used_ai`, `requires_review`, `legacy_mapping`, `schema_type`), `mappings_approved`, `transform_queued`, and `transform_completed` (with `schema_type` where applicable)
- CSV files only (no XLSX)
- Async analyze/transform jobs via Celery
- No frontend/dashboard/billing/team features

## Engineering Principles

- Prefer boring, explicit, maintainable code over cleverness.
- Keep strict layer boundaries:
  - `api` (transport)
  - `services` (business logic)
  - `models` (persistence)
  - `schemas` (contracts)
  - `workers` (async orchestration)
  - `utils` (small pure helpers)
- Keep modules small and cohesive.
- Add comments only for non-obvious logic.
- Preserve existing behavior unless change is requested.

## Operational Guardrails

- Auth: `/api/v1/imports/*` and `/api/v1/templates/*` require `X-API-Key`.
- Rate limit: keep Redis-backed rate limiting behavior intact.
- Storage: keep storage behind interface (`local` and `s3` adapters).
- Status lifecycle must remain valid:
  - Non-template: `created -> uploaded -> analyzing -> analyzed -> transforming -> completed|failed`
  - Template-driven: `created -> uploaded -> analyzing -> needs_review|ready_to_transform -> (approve-mappings) -> ready_to_transform -> transforming -> completed|failed`
  - `analyzed` remains for legacy imports without a template snapshot
  - When mappings are finalized for a template-bound import (`ready_to_transform` after auto-accept or after `approve-mappings`), the API records `mappings_finalized_at`, increments `final_mapping_revision`, and appends rows to `import_final_mappings` for auditing

## Local Runtime and Quality Gates

Before finalizing non-trivial changes:

1. Ensure stack is up
   - `make dev` (or `docker compose up -d --build`)
2. Ensure DB schema is current
   - `make migrate` (or `docker compose run --rm api alembic upgrade head`)
3. Run tests
   - `make test` (or `docker compose run --rm -e TEST_BASE_URL=http://api:8000 api pytest -q`)
4. Verify health and metrics paths
   - `/health`, `/health/live`, `/health/ready`, `/api/v1/metrics`
5. Update docs if behavior/commands changed

## Monorepo Root Commands

- Primary workflow is through root `Makefile`.
- `make web` is a Phase 3 placeholder until `apps/web` is added in Phase 4.
- `make docs-sync` is a Phase 3 placeholder until OpenAPI sync is added in Phase 5.

## Versioning Rules

- Semantic Versioning (`MAJOR.MINOR.PATCH`)
- Source of truth: `apps/api/pyproject.toml` `[project].version`
- Use automation script:
  - `python scripts/version.py patch|minor|major`
  - add `--git` to auto-commit and tag
- Tag format: `vX.Y.Z`
- Release commit format: `release: vX.Y.Z`

## Release and Docs Checklist

For any behavior-changing PR:

1. Update implementation and tests.
2. Update `README.md` and relevant `docs/*.md`.
3. Validate all commands in docs still work.
4. Confirm status lifecycle and auth/rate-limit semantics are still accurate.
5. If releasing, bump version with `scripts/version.py` and tag.

## Documentation Rules

- `README.md` must stay runnable for a solo developer on Docker.
- Every new operational command should be documented in `README.md` and linked runbooks.
- Keep examples realistic and copy-paste friendly.
- Do not leave stale endpoint/status/config docs after behavior changes.
