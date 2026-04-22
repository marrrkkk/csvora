import csv
import io
from typing import Any

from app.models.template import TemplateField
from app.services.transform.normalizers import (
    normalize_country,
    normalize_email,
    normalize_phone,
    normalize_tags,
    normalize_whitespace,
)
from app.services.transform.rule_runner import (
    apply_default,
    field_emits_list,
    is_empty_schema_row,
    is_value_empty,
    normalize_cell,
    validate_field_value,
    validate_template_level_rules,
)
from app.services.transform.validators import is_empty_contact_row, is_valid_email, is_valid_phone

# Built-in contact columns for legacy non-template transforms.
CANONICAL_FIELDS = [
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone",
    "company",
    "job_title",
    "city",
    "state",
    "country",
    "tags",
    "notes",
]


def _legacy_contact_transform(csv_bytes: bytes, mappings: dict[str, str]) -> dict[str, object]:
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    output_fields = sorted(set(mappings.values()))
    cleaned_rows: list[dict[str, object]] = []
    normalized_rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    valid_count = 0
    invalid_count = 0
    skipped_row_count = 0
    missing_mapping_columns: set[str] = set()

    for source_column, target_field in mappings.items():
        if source_column not in headers:
            missing_mapping_columns.add(source_column)
            issues.append(
                {
                    "row_number": None,
                    "field_name": source_column,
                    "severity": "error",
                    "message": "Mapped source column not found in file",
                }
            )

    for row_idx, source_row in enumerate(reader, start=2):
        canonical_row: dict[str, object] = {}
        for field in output_fields:
            canonical_row[field] = [] if field == "tags" else None

        for source_column, target_field in mappings.items():
            if source_column in missing_mapping_columns:
                continue
            value = source_row.get(source_column)
            if value is None:
                continue
            if target_field == "tags":
                canonical_row["tags"] = normalize_tags(value)
            elif target_field == "email":
                canonical_row["email"] = normalize_email(value)
            elif target_field == "phone":
                canonical_row["phone"] = normalize_phone(value)
            elif target_field == "country":
                canonical_row["country"] = normalize_country(value)
            else:
                canonical_row[target_field] = normalize_whitespace(value)

        if "full_name" in canonical_row and not canonical_row.get("full_name"):
            first = (canonical_row.get("first_name") or "") if isinstance(canonical_row.get("first_name"), str) else ""
            last = (canonical_row.get("last_name") or "") if isinstance(canonical_row.get("last_name"), str) else ""
            full_name = normalize_whitespace(f"{first} {last}".strip())
            canonical_row["full_name"] = full_name

        if is_empty_contact_row(canonical_row):
            skipped_row_count += 1
            issues.append(
                {
                    "row_number": row_idx,
                    "field_name": None,
                    "severity": "warning",
                    "message": "Row skipped because it is empty after normalization",
                }
            )
            continue

        row_valid = True
        if "email" in canonical_row or "phone" in canonical_row:
            if not canonical_row.get("email") and not canonical_row.get("phone"):
                issues.append(
                    {
                        "row_number": row_idx,
                        "field_name": None,
                        "severity": "error",
                        "message": "Row requires at least email or phone",
                    }
                )
                row_valid = False

        email = canonical_row.get("email")
        if isinstance(email, str) and email and not is_valid_email(email):
            issues.append(
                {"row_number": row_idx, "field_name": "email", "severity": "error", "message": "Invalid email format"}
            )
            row_valid = False

        phone = canonical_row.get("phone")
        if isinstance(phone, str) and phone and not is_valid_phone(phone):
            issues.append(
                {"row_number": row_idx, "field_name": "phone", "severity": "warning", "message": "Phone format unusual"}
            )

        cleaned_rows.append(canonical_row)
        normalized_rows.append(canonical_row)
        if row_valid:
            valid_count += 1
        else:
            invalid_count += 1

    return {
        "cleaned_rows": cleaned_rows,
        "normalized_rows": normalized_rows,
        "issues": issues,
        "valid_row_count": valid_count,
        "invalid_row_count": invalid_count,
        "skipped_row_count": skipped_row_count,
        "output_fieldnames": output_fields,
    }


def _schema_driven_transform(
    csv_bytes: bytes,
    mappings: dict[str, str],
    fields_by_key: dict[str, TemplateField],
    template_validation_rules: dict[str, Any] | None,
) -> dict[str, object]:
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    issues: list[dict[str, object]] = []
    missing_mapping_columns: set[str] = set()

    for source_column, target_field in mappings.items():
        if source_column not in headers:
            missing_mapping_columns.add(source_column)
            issues.append(
                {
                    "row_number": None,
                    "field_name": source_column,
                    "severity": "error",
                    "message": "Mapped source column not found in file",
                }
            )

    for tgt in set(mappings.values()):
        if tgt not in fields_by_key:
            issues.append(
                {
                    "row_number": None,
                    "field_name": tgt,
                    "severity": "error",
                    "message": "Mapped target_field is not defined on the template version",
                }
            )

    effective_mappings = {s: t for s, t in mappings.items() if t in fields_by_key and s not in missing_mapping_columns}
    output_fields = sorted(set(effective_mappings.values()))

    cleaned_rows: list[dict[str, object]] = []
    normalized_rows: list[dict[str, object]] = []
    valid_count = 0
    invalid_count = 0
    skipped_row_count = 0

    for row_idx, source_row in enumerate(reader, start=2):
        row: dict[str, Any] = {}
        for fk in output_fields:
            f = fields_by_key[fk]
            row[fk] = [] if field_emits_list(f) else None

        for source_column, target_field in effective_mappings.items():
            value = source_row.get(source_column)
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            raw = value if isinstance(value, str) else str(value)
            field = fields_by_key[target_field]
            norm = normalize_cell(field, raw)
            prev = row.get(target_field)
            if field_emits_list(field) and isinstance(prev, list) and isinstance(norm, list):
                merged = list(prev)
                for x in norm:
                    if x not in merged:
                        merged.append(x)
                row[target_field] = merged
            else:
                row[target_field] = norm

        for fk in output_fields:
            row[fk] = apply_default(fields_by_key[fk], row.get(fk))

        if "full_name" in output_fields and fields_by_key.get("full_name"):
            fn = row.get("full_name")
            if is_value_empty(fn) and "first_name" in output_fields and "last_name" in output_fields:
                first = row.get("first_name") or ""
                last = row.get("last_name") or ""
                if isinstance(first, str) and isinstance(last, str):
                    row["full_name"] = normalize_whitespace(f"{first} {last}".strip())

        if is_empty_schema_row(row, output_fields):
            skipped_row_count += 1
            issues.append(
                {
                    "row_number": row_idx,
                    "field_name": None,
                    "severity": "warning",
                    "message": "Row skipped because it is empty after normalization",
                }
            )
            continue

        row_valid = True
        for issue in validate_template_level_rules(row, template_validation_rules, row_idx):
            issues.append(issue)
            if issue.get("severity") == "error":
                row_valid = False

        for fk in output_fields:
            for issue in validate_field_value(fields_by_key[fk], row.get(fk), row_idx):
                issues.append(issue)
                if issue.get("severity") == "error":
                    row_valid = False

        cleaned_rows.append(row)
        normalized_rows.append(row)
        if row_valid:
            valid_count += 1
        else:
            invalid_count += 1

    return {
        "cleaned_rows": cleaned_rows,
        "normalized_rows": normalized_rows,
        "issues": issues,
        "valid_row_count": valid_count,
        "invalid_row_count": invalid_count,
        "skipped_row_count": skipped_row_count,
        "output_fieldnames": output_fields,
    }


def run_transform(
    csv_bytes: bytes,
    mappings: dict[str, str],
    *,
    fields_by_key: dict[str, TemplateField] | None = None,
    template_validation_rules: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Transform CSV rows using either legacy contact heuristics or template field metadata."""
    if fields_by_key is None:
        return _legacy_contact_transform(csv_bytes, mappings)
    return _schema_driven_transform(csv_bytes, mappings, fields_by_key, template_validation_rules)
