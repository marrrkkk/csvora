import uuid

from app.models.enums import TemplateFieldValueType
from app.models.template import TemplateField, TemplateVersion
from app.services.analyzer.file_analyzer import analyze_csv_bytes


def test_analyze_csv_bytes_basic() -> None:
    csv_bytes = b"first_name,last_name,email,phone\nJane,Doe,jane@example.com,+1-202-555-0100\n"
    result = analyze_csv_bytes(csv_bytes, preview_rows=5, sample_lines=10)

    assert result["legacy_contact_mapping"] is True
    assert result["delimiter"] == ","
    assert result["header_row_index"] == 0
    assert result["total_rows"] == 1
    assert "email" in result["source_columns"]

    suggestions = result["mapping_suggestions"]
    assert any(s["target_field"] == "email" for s in suggestions)
    assert any(s["target_field"] == "phone" for s in suggestions)


def test_analyze_csv_with_blank_preamble() -> None:
    csv_bytes = b"\n\nfirst_name,last_name,email\nJane,Doe,jane@example.com\n"
    result = analyze_csv_bytes(csv_bytes, preview_rows=5, sample_lines=10)
    assert result["header_row_index"] == 2
    assert result["total_rows"] == 1


def test_analyze_csv_bytes_with_template_is_not_legacy_mapping() -> None:
    tv_id = uuid.uuid4()
    tv = TemplateVersion(
        id=tv_id,
        template_id=uuid.uuid4(),
        version=1,
        strict_mode=False,
        auto_accept_confidence=0.9,
        review_threshold=0.7,
        ai_enabled=False,
    )
    tv.fields = [
        TemplateField(
            template_version_id=tv_id,
            field_key="email",
            label="Email",
            value_type=TemplateFieldValueType.EMAIL,
            is_builtin=True,
            is_required=False,
            aliases=["mail"],
            allow_empty=True,
            sort_order=0,
        )
    ]
    csv_bytes = b"mail\njane@example.com\n"
    result = analyze_csv_bytes(csv_bytes, preview_rows=5, sample_lines=10, template_version=tv, ai_settings=None)
    assert result["legacy_contact_mapping"] is False
    assert result["template_version_id"] == str(tv.id)


def test_analyze_csv_with_multiline_quoted_field() -> None:
    csv_bytes = (
        b'first_name,last_name,email,notes\n"Jane","Doe","jane@example.com","Line one\nLine two"\n'
        b'"Bob","Smith","bob@example.com","Single line"\n'
    )
    result = analyze_csv_bytes(csv_bytes, preview_rows=5, sample_lines=10)
    assert result["total_rows"] == 2
    assert "notes" in result["source_columns"]

