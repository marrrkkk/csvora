from types import SimpleNamespace

from app.models.enums import TemplateFieldValueType
from app.services.transform.transformer import run_transform


def _field(
    field_key: str,
    value_type: TemplateFieldValueType,
    *,
    is_required: bool = False,
    allow_empty: bool = True,
    default_value: object | None = None,
    validation_rules: dict | None = None,
    normalizer_config: dict | None = None,
    enum_values: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        field_key=field_key,
        label=field_key,
        value_type=value_type,
        is_builtin=False,
        is_required=is_required,
        allow_empty=allow_empty,
        default_value=default_value,
        validation_rules=validation_rules,
        normalizer_config=normalizer_config,
        enum_values=enum_values,
    )


def test_transform_requires_email_or_phone() -> None:
    csv_bytes = b"first_name,last_name,email,phone\nJane,Doe,,\n"
    mappings = {"first_name": "first_name", "last_name": "last_name", "email": "email", "phone": "phone"}
    result = run_transform(csv_bytes, mappings)
    assert result["valid_row_count"] == 0
    assert result["invalid_row_count"] == 1
    assert any(i["message"] == "Row requires at least email or phone" for i in result["issues"])


def test_transform_normalizes_email_and_tags() -> None:
    csv_bytes = b"email,tags\n  Jane@Example.com  ,a; A ;b\n"
    mappings = {"email": "email", "tags": "tags"}
    result = run_transform(csv_bytes, mappings)
    row = result["normalized_rows"][0]
    assert row["email"] == "jane@example.com"
    assert row["tags"] == ["a", "b"]


def test_transform_emits_missing_mapping_column_issue() -> None:
    csv_bytes = b"email\njane@example.com\n"
    mappings = {"missing_column": "phone"}
    result = run_transform(csv_bytes, mappings)
    assert any(i["message"] == "Mapped source column not found in file" for i in result["issues"])


def test_transform_emits_empty_row_skip_warning() -> None:
    csv_bytes = b"email,phone\n,\n"
    mappings = {"email": "email", "phone": "phone"}
    result = run_transform(csv_bytes, mappings)
    assert result["skipped_row_count"] == 1
    assert any(i["message"] == "Row skipped because it is empty after normalization" for i in result["issues"])


def test_schema_driven_transform_validates_required() -> None:
    csv_bytes = b"sku,title\n,hello\n"
    mappings = {"sku": "sku", "title": "title"}
    fields_by_key = {
        "sku": _field("sku", TemplateFieldValueType.STRING, is_required=True, allow_empty=False),
        "title": _field("title", TemplateFieldValueType.STRING),
    }
    result = run_transform(csv_bytes, mappings, fields_by_key=fields_by_key, template_validation_rules=None)
    assert result["skipped_row_count"] == 0
    assert result["invalid_row_count"] == 1
    assert any("required" in str(i.get("message", "")).lower() for i in result["issues"])


def test_schema_driven_require_one_of_template_rule() -> None:
    csv_bytes = b"a,b,c\n,,ok\n"
    mappings = {"a": "field_a", "b": "field_b", "c": "field_c"}
    fields_by_key = {
        "field_a": _field("field_a", TemplateFieldValueType.STRING),
        "field_b": _field("field_b", TemplateFieldValueType.STRING),
        "field_c": _field("field_c", TemplateFieldValueType.STRING),
    }
    rules = {"require_one_of": [["field_a", "field_b"]]}
    result = run_transform(csv_bytes, mappings, fields_by_key=fields_by_key, template_validation_rules=rules)
    assert result["valid_row_count"] == 0
    assert any("at least one value" in str(i.get("message", "")) for i in result["issues"])


def test_schema_driven_contacts_compat_still_normalizes_email() -> None:
    csv_bytes = b"mail\nTest@EXAMPLE.com\n"
    mappings = {"mail": "email"}
    fields_by_key = {"email": _field("email", TemplateFieldValueType.EMAIL)}
    result = run_transform(csv_bytes, mappings, fields_by_key=fields_by_key)
    assert result["normalized_rows"][0]["email"] == "test@example.com"
