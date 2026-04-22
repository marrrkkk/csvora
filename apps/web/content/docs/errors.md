# Errors

The API returns JSON errors with appropriate HTTP status codes.

## Common cases

- `401`: missing API key
- `403`: invalid/revoked/expired API key
- `404`: import not found (or not owned by your API key)
- `409`: duplicate analyze/transform trigger (already in progress)
- `422`: validation errors (e.g., invalid transform mappings)

## Validation errors (422)

Mapping requests are strictly validated:

- at least one mapping is required
- no duplicate `source_column`
- no duplicate `target_field`
- canonical target fields only

