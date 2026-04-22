# Import lifecycle

Imports progress through a state machine. Paths depend on whether the import was created with a `template_id`.

## Non-template (legacy) flow

- `created`
- `uploaded`
- `analyzing`
- `analyzed`
- `transforming`
- `completed` (terminal)
- `failed` (terminal)

Client supplies mappings on `POST /api/v1/imports/{id}/transform`.

## Template-driven flow

- `created` (with `template_id` / frozen `template_version_id`)
- `uploaded`
- `analyzing`
- `needs_review` — mapping confidence or strict-mode rules require developer approval
- `ready_to_transform` — mappings finalized (auto-accepted or after `approve-mappings`)
- `transforming`
- `completed` (terminal)
- `failed` (terminal)

Use `POST /api/v1/imports/{id}/approve-mappings` when status is `needs_review`.  
When status is `ready_to_transform`, `POST /api/v1/imports/{id}/transform` may use an empty JSON body `{}`; mappings are read from the database.

## Endpoints

- `POST /api/v1/templates` … (see root `README.md`)
- `POST /api/v1/imports`
- `POST /api/v1/imports/{id}/upload`
- `POST /api/v1/imports/{id}/analyze`
- `GET /api/v1/imports/{id}/status`
- `GET /api/v1/imports/{id}/analysis`
- `POST /api/v1/imports/{id}/approve-mappings`
- `POST /api/v1/imports/{id}/transform`
- `GET /api/v1/imports/{id}/result`

## Idempotency notes

- Duplicate analyze/transform triggers return `409` and should not enqueue duplicate work.
