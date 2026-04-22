# Configuration Reference

All configuration is environment-driven. Start from `.env.example` and override values per environment.

## Application

- `APP_NAME` (default: `CSV Import Fixer API`): service name
- `APP_ENV` (default: `development`): environment label
- `APP_DEBUG` (default: `true`): debug behavior toggle
- `API_HOST` (default: `0.0.0.0`): API bind host
- `API_PORT` (default: `8000`): API bind port
- `API_PREFIX` (default: `/api/v1`): versioned API route prefix

## Database

- `POSTGRES_HOST` (default: `postgres`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_USER` (default: `csv_import_fixer`)
- `POSTGRES_PASSWORD` (default: `csv_import_fixer`)
- `POSTGRES_DB` (default: `csv_import_fixer`)
- `DATABASE_URL` (default: empty): optional full SQLAlchemy DSN override

## Redis and Celery

- `REDIS_HOST` (default: `redis`)
- `REDIS_PORT` (default: `6379`)
- `REDIS_DB` (default: `0`)
- `REDIS_URL` (default: `redis://redis:6379/0`)
- `CELERY_BROKER_URL` (default: `redis://redis:6379/0`)
- `CELERY_RESULT_BACKEND` (default: `redis://redis:6379/1`)

## Upload and Storage

- `MAX_UPLOAD_SIZE_BYTES` (default: `10485760`): max upload size in bytes
- `STORAGE_BACKEND` (default: `local`): `local` or `s3`
- `LOCAL_STORAGE_ROOT` (default: `/data/storage`)
- `S3_ENDPOINT_URL` (default: empty)
- `S3_ACCESS_KEY_ID` (default: empty)
- `S3_SECRET_ACCESS_KEY` (default: empty)
- `S3_REGION` (default: `us-east-1`)
- `S3_BUCKET_NAME` (default: `csv-import-fixer`)
- `S3_USE_SSL` (default: `false`)

## Analyze and Transform

- `ANALYSIS_PREVIEW_ROWS` (default: `10`): preview rows returned in analysis
- `ANALYSIS_SAMPLE_LINES` (default: `50`): sampling depth for detection/inference
- `TRANSFORM_PHONE_WARNING_IS_ERROR` (default: `false`): promote phone warnings to errors
- `IMPORT_REQUIRES_TEMPLATE` (default: `false`): when `true`, `POST /imports` rejects requests without `template_id`

## Logging, Auth, and Rate Limiting

- `LOG_LEVEL` (default: `INFO`)
- `AUTH_ENABLED` (default: `true`): protect import routes
- `RATE_LIMIT_ENABLED` (default: `true`)
- `RATE_LIMIT_PER_MINUTE` (default: `120`): per-route limit
- `RATE_LIMIT_GLOBAL_PER_MINUTE` (default: `300`): cross-route limit
- `RATE_LIMIT_WINDOW_SECONDS` (default: `60`)
- `RATE_LIMIT_FAIL_OPEN` (default: `true`): allow requests when Redis limiter errors
- `RATE_LIMIT_REDIS_TIMEOUT_MS` (default: `250`): limiter Redis timeout

## Optional AI (mapping assist only)

- `OPENROUTER_API_KEY` (default: empty): when set with `AI_MAPPING_ENABLED=true`, analyze may call OpenRouter for ranking hints
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)
- `OPENROUTER_MODEL` (default: `openai/gpt-4o-mini`)
- `OPENROUTER_HTTP_REFERER` (default: `https://csvora.local`)
- `OPENROUTER_APP_TITLE` (default: `Csvora API`)
- `AI_MAPPING_ENABLED` (default: `false`): master switch; templates also set per-version `ai_enabled`
- `AI_TIMEOUT_SECONDS` (default: `20`)
- `AI_MAX_RETRIES` (default: `1`)

## Observability and Readiness

- `METRICS_ENABLED` (default: `true`)
- `READINESS_DB_TIMEOUT_MS` (default: `500`)
- `READINESS_REDIS_TIMEOUT_MS` (default: `500`)
- `READINESS_STORAGE_TIMEOUT_MS` (default: `500`)

## Operational Guidance

- Keep `RATE_LIMIT_FAIL_OPEN=true` unless strict fail-closed behavior is required.
- Keep readiness timeouts low to avoid stuck probes.
- For local Docker, default values are designed to work without modification.
