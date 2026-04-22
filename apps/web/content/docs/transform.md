# Transform flow

Transform applies approved mappings, normalizes values, validates rows, and generates artifacts.

## Submit mappings

```bash
curl -X POST "http://localhost:8000/api/v1/imports/<import_id>/transform" \
  -H "X-API-Key: <RAW_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": [
      {"source_column": "email", "target_field": "email"},
      {"source_column": "phone", "target_field": "phone"}
    ]
  }'
```

## Data safety notes

- Missing mapped source columns produce explicit issues.
- Empty rows after normalization are skipped (warning).
- Phone warnings may be promoted to errors via `TRANSFORM_PHONE_WARNING_IS_ERROR=true`.

