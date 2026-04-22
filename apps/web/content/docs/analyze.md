# Analyze flow

Analyze detects CSV structure and proposes mapping suggestions.

## Trigger analyze

```bash
curl -X POST "http://localhost:8000/api/v1/imports/<import_id>/analyze" \
  -H "X-API-Key: <RAW_KEY>"
```

## Poll status

```bash
curl "http://localhost:8000/api/v1/imports/<import_id>/status" \
  -H "X-API-Key: <RAW_KEY>"
```

## Fetch analysis

```bash
curl "http://localhost:8000/api/v1/imports/<import_id>/analysis" \
  -H "X-API-Key: <RAW_KEY>"
```

