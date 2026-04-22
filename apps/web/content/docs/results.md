# Result retrieval

After transform completes, fetch the result payload and artifact references.

```bash
curl "http://localhost:8000/api/v1/imports/<import_id>/result" \
  -H "X-API-Key: <RAW_KEY>"
```

## What you get

- counts (valid/invalid rows)
- artifact keys/URLs (cleaned CSV, normalized JSON, validation report)
- row-level issues (errors and warnings)

