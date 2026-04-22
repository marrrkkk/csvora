"""Template-driven normalization and validation for schema-aware transforms."""

from __future__ import annotations

import copy
import re
from datetime import date
from typing import Any

from app.models.enums import TemplateFieldValueType
from app.models.template import TemplateField
from app.services.transform.normalizers import (
    normalize_country,
    normalize_email,
    normalize_phone,
    normalize_tags,
    normalize_whitespace,
)
from app.services.transform.validators import is_valid_email, is_valid_phone


def is_value_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, (int, float)) and value == 0:
        return False
    if isinstance(value, bool):
        return False
    return False


def field_emits_list(field: TemplateField) -> bool:
    nc = field.normalizer_config or {}
    return nc.get("kind") == "tags_list" or nc.get("as") == "list"


def normalize_cell(field: TemplateField, raw: str | None) -> Any:
    if field_emits_list(field):
        return normalize_tags(raw)

    vt = field.value_type
    if vt is TemplateFieldValueType.EMAIL:
        return normalize_email(raw)
    if vt is TemplateFieldValueType.PHONE:
        return normalize_phone(raw)
    if vt is TemplateFieldValueType.STRING:
        if (field.normalizer_config or {}).get("kind") == "country":
            return normalize_country(raw)
        return normalize_whitespace(raw)
    if vt is TemplateFieldValueType.INT:
        s = normalize_whitespace(raw)
        if s is None:
            return None
        try:
            return int(s, 10)
        except ValueError:
            return None
    if vt is TemplateFieldValueType.FLOAT:
        s = normalize_whitespace(raw)
        if s is None:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    if vt is TemplateFieldValueType.BOOL:
        s = (normalize_whitespace(raw) or "").lower()
        if not s:
            return None
        if s in {"1", "true", "yes", "y", "on"}:
            return True
        if s in {"0", "false", "no", "n", "off"}:
            return False
        return None
    if vt is TemplateFieldValueType.DATE:
        s = normalize_whitespace(raw)
        if s is None:
            return None
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            return None
    if vt is TemplateFieldValueType.ENUM:
        return normalize_whitespace(raw)
    return normalize_whitespace(raw)


def apply_default(field: TemplateField, value: Any) -> Any:
    if is_value_empty(value) and field.default_value is not None:
        return copy.deepcopy(field.default_value)
    return value


def is_empty_schema_row(row: dict[str, object], output_fields: list[str]) -> bool:
    for k in output_fields:
        if not is_value_empty(row.get(k)):
            return False
    return True


def validate_template_level_rules(
    row: dict[str, Any],
    template_rules: dict[str, Any] | None,
    row_idx: int,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if not template_rules:
        return issues
    groups = template_rules.get("require_one_of") or []
    for group in groups:
        if not isinstance(group, (list, tuple)):
            continue
        keys = [str(k) for k in group if isinstance(k, str)]
        if not keys:
            continue
        if any(not is_value_empty(row.get(k)) for k in keys):
            continue
        issues.append(
            {
                "row_number": row_idx,
                "field_name": None,
                "severity": "error",
                "message": f"Row requires at least one value among: {', '.join(keys)}",
            }
        )
    return issues


def validate_field_value(field: TemplateField, value: Any, row_idx: int) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    fk = field.field_key

    if field.is_required and is_value_empty(value):
        issues.append(
            {
                "row_number": row_idx,
                "field_name": fk,
                "severity": "error",
                "message": f"Field {fk} is required",
            }
        )
        return issues

    if not field.allow_empty and is_value_empty(value):
        issues.append(
            {
                "row_number": row_idx,
                "field_name": fk,
                "severity": "error",
                "message": f"Field {fk} cannot be empty",
            }
        )
        return issues

    if is_value_empty(value):
        return issues

    rules = field.validation_rules or {}
    if isinstance(value, str):
        if "min_length" in rules:
            mn = int(rules["min_length"])
            if len(value) < mn:
                issues.append(
                    {
                        "row_number": row_idx,
                        "field_name": fk,
                        "severity": "error",
                        "message": f"Field {fk} is shorter than min_length {mn}",
                    }
                )
        if "max_length" in rules:
            mx = int(rules["max_length"])
            if len(value) > mx:
                issues.append(
                    {
                        "row_number": row_idx,
                        "field_name": fk,
                        "severity": "error",
                        "message": f"Field {fk} exceeds max_length {mx}",
                    }
                )
        pat = rules.get("regex")
        if isinstance(pat, str) and pat:
            try:
                if not re.search(pat, value):
                    issues.append(
                        {
                            "row_number": row_idx,
                            "field_name": fk,
                            "severity": "error",
                            "message": f"Field {fk} failed regex validation",
                        }
                    )
            except re.error:
                pass

    if field.value_type is TemplateFieldValueType.ENUM and field.enum_values:
        allowed = {str(x).casefold() for x in field.enum_values}
        if str(value).casefold() not in allowed:
            issues.append(
                {
                    "row_number": row_idx,
                    "field_name": fk,
                    "severity": "error",
                    "message": f"Field {fk} must be one of: {', '.join(str(x) for x in field.enum_values)}",
                }
            )

    if field.value_type is TemplateFieldValueType.EMAIL and isinstance(value, str) and value and not is_valid_email(value):
        issues.append(
            {
                "row_number": row_idx,
                "field_name": fk,
                "severity": "error",
                "message": "Invalid email format",
            }
        )

    if field.value_type is TemplateFieldValueType.PHONE and isinstance(value, str) and value and not is_valid_phone(value):
        issues.append(
            {
                "row_number": row_idx,
                "field_name": fk,
                "severity": "warning",
                "message": "Phone format unusual",
            }
        )

    return issues
