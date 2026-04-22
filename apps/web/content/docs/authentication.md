# Authentication

All `/api/v1/imports/*` endpoints require an API key in the `X-API-Key` header.

## Requests

```bash
curl -H "X-API-Key: <RAW_KEY>" http://localhost:8000/api/v1/imports/<import_id>
```

## Expected behavior

- Missing key: `401`
- Invalid/revoked/expired key: `403`

## Key lifecycle (operator notes)

API keys are stored in Postgres and support:

- `is_active`
- `revoked_at`
- `expires_at`

