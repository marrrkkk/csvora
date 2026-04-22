# Deploy and Rollback Runbook

## Deploy Checklist

1. Ensure branch is green:
   - unit + integration tests pass
2. Confirm migrations are included for schema changes.
3. Review config deltas against `docs/config-reference.md`.
4. Build and publish image.
5. Run migrations in target environment before serving traffic.
6. Validate post-deploy health:
   - `/health/live`
   - `/health/ready`
   - `/api/v1/metrics`

## Migration Safety

- Prefer additive schema changes.
- For destructive migrations, plan staged rollout:
  - deploy code that no longer depends on old columns,
  - then remove columns in a later migration.
- Verify unique constraints and backfills on a staging snapshot first.

## Rollback Decision Tree

- If deploy fails before migrations:
  - roll back application image to previous version.
- If deploy fails after additive migrations:
  - roll back app image; keep schema forward-compatible.
- If deploy includes non-backward-compatible migration:
  - do not auto-downgrade blindly,
  - assess data impact and use an explicit, tested rollback script.

## Post-Deploy Verification

- Health endpoints return `200`.
- Create/import/analyze/transform flow works with valid API key.
- No sustained spikes in:
  - `429` responses
  - failed Celery tasks
  - readiness failures

## Release Versioning

- Bump version:
  - `python scripts/version.py patch|minor|major`
- For automated release commit/tag:
  - `python scripts/version.py patch --git`
- Tag format:
  - `vX.Y.Z`
