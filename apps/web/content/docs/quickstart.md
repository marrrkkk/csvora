# Quickstart

Run everything locally with Docker, then use the API with an `X-API-Key`.

## Start the backend

From the repo root:

```bash
cp .env.example .env
docker compose up -d --build
docker compose run --rm api alembic upgrade head
```

## Create an API key (local dev)

Generate a raw key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

From the repo root, hash the key and compute the prefix:

```bash
RAW_KEY="<RAW_KEY>" docker compose run --rm api python -c "from app.core.security import hash_api_key, build_key_prefix; import os; raw=os.environ['RAW_KEY']; print(build_key_prefix(raw)); print(hash_api_key(raw))"
```

Insert into Postgres:

```bash
docker compose exec -T postgres psql -U csv_import_fixer -d csv_import_fixer -c "insert into api_keys (id, key_prefix, key_hash, name, is_active) values ('<UUID>', '<KEY_PREFIX>', '<KEY_HASH>', 'local-dev', true);"
```

## Try the API flow

```bash
# 1) Create import
curl -X POST http://localhost:8000/api/v1/imports \
  -H "X-API-Key: <RAW_KEY>" \
  -H "Content-Type: application/json" \
  -d "{\"original_filename\":\"contacts.csv\"}"

# 2) Upload CSV
curl -X POST "http://localhost:8000/api/v1/imports/<import_id>/upload" \
  -H "X-API-Key: <RAW_KEY>" \
  -F "file=@./contacts.csv;type=text/csv"

# 3) Analyze
curl -X POST "http://localhost:8000/api/v1/imports/<import_id>/analyze" \
  -H "X-API-Key: <RAW_KEY>"

# 4) Transform
curl -X POST "http://localhost:8000/api/v1/imports/<import_id>/transform" \
  -H "X-API-Key: <RAW_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"mappings":[{"source_column":"email","target_field":"email"}]}'

# 5) Result
curl "http://localhost:8000/api/v1/imports/<import_id>/result" \
  -H "X-API-Key: <RAW_KEY>"
```

