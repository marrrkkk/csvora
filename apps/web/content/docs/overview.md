# Overview

**Csvora** is a developer-first API that turns messy CSV files into clean, import-ready artifacts using **reusable import templates** (versioned schemas you define), deterministic validation, and optional AI-assisted mapping suggestions.

## What it does

- Accepts CSV uploads; each template declares a `schema_type` (for example `contacts` or `products`) and the fields for that schema.
- Lets you define **templates**: fields, aliases, required flags, confidence thresholds, and per-version `strict_mode` / `ai_enabled`.
- Analyzes file structure (delimiter/encoding/header) and proposes **template-scoped** mappings with auto-accept vs `needs_review`.
- Lets clients finalize mappings (`approve-mappings`) when review is required.
- Transforms data using the template’s field definitions (`value_type`, `normalizer_config`, `validation_rules`, and optional version-level `validation_rules` such as `require_one_of`).
- Normalizes and validates rows and produces row-level issues.
- Stores and returns artifact references:
  - cleaned CSV
  - normalized JSON
  - validation report

## Example: contacts built-ins (legacy vocabulary)

The non-template import path and many starter templates still use this common set:

- first_name
- last_name
- full_name
- email
- phone
- company
- job_title
- city
- state
- country
- tags
- notes

Additional fields are declared on the template version and emitted as output columns.

## Import status lifecycle

| Path | Typical sequence |
|------|-------------------|
| **Without template** | `created` → `uploaded` → `analyzing` → `analyzed` → `transforming` → `completed` (or `failed`). Analysis sets `legacy_contact_mapping: true` in the stored payload. |
| **With template** | `created` → `uploaded` → `analyzing` → `needs_review` **or** `ready_to_transform` → (optional `approve-mappings`) → `ready_to_transform` → `transforming` → `completed`. When mappings are finalized for a template import, `mappings_finalized_at` and `final_mapping_revision` update; poll `GET /imports/{id}/status` for those fields. |

## High-level flow

- Create template (optional but recommended for repeatable imports)
- Create import (`template_id` optional)
- Upload CSV
- Analyze (async)
- If `needs_review`: approve mappings; when `ready_to_transform`, proceed
- Transform (async)
- Fetch result and artifact references

AI never overrides template constraints; it only refines candidate ranking when enabled.
