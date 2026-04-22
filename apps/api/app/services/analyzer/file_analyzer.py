import io
from typing import Any

import polars as pl

from app.models.template import TemplateVersion
from app.services.analyzer.mapping_inference import infer_mapping
from app.services.analyzer.template_mapping import TemplateMappingContext, infer_template_mappings
from app.services.ai.mapping_assist import maybe_enhance_analysis_with_ai
from app.utils.csv_detection import detect_delimiter, detect_encoding, detect_header_row


def analyze_csv_bytes(
    file_bytes: bytes,
    preview_rows: int,
    sample_lines: int,
    *,
    template_version: TemplateVersion | None = None,
    ai_settings: Any | None = None,
) -> dict[str, object]:
    encoding, warnings = detect_encoding(file_bytes)
    decoded = file_bytes.decode(encoding, errors="replace")
    lines = decoded.splitlines()
    delimiter = detect_delimiter(decoded, sample_lines=sample_lines)
    header_row_index = detect_header_row(lines=lines, delimiter=delimiter)

    csv_portion = "\n".join(lines[header_row_index:])
    frame = pl.read_csv(io.StringIO(csv_portion), separator=delimiter, infer_schema_length=100)

    columns = frame.columns
    preview = frame.head(preview_rows).to_dicts()

    base: dict[str, object] = {
        "delimiter": delimiter,
        "encoding": encoding,
        "header_row_index": header_row_index,
        "total_rows": frame.height,
        "source_columns": columns,
        "preview_rows": preview,
        "warnings": warnings,
        "template_version_id": str(template_version.id) if template_version else None,
        "ai_mapping_used": False,
        # True when mappings use legacy contact CANONICAL_FIELDS (no template); False when template-scored.
        "legacy_contact_mapping": template_version is None,
    }

    if template_version is not None:
        fields = list(template_version.fields)
        ctx = TemplateMappingContext(
            template_version=template_version,
            auto_accept_confidence=float(template_version.auto_accept_confidence),
            review_threshold=float(template_version.review_threshold),
            strict_mode=bool(template_version.strict_mode),
        )
        tm = infer_template_mappings(columns, preview, ctx)
        base.update(tm)
        if ai_settings is not None and template_version.ai_enabled:
            keys = [f.field_key for f in fields]
            base_dict = {k: base[k] for k in base}
            enhanced, used = maybe_enhance_analysis_with_ai(
                ai_settings,
                base_dict,
                template_field_keys=keys,
                template_fields=fields,
                ctx=ctx,
                ai_enabled_on_template=True,
            )
            base.update(enhanced)
            base["ai_mapping_used"] = used
    else:
        mappings = infer_mapping(columns)
        base["mapping_suggestions"] = mappings
        base["mapping_candidates"] = [
            {
                "source_column": m["source_column"],
                "target_field": m["target_field"],
                "confidence": m["confidence"],
                "reason": m.get("reason"),
                "candidates": [],
            }
            for m in mappings
        ]
        base["auto_approved_mappings"] = []
        base["requires_review"] = False
        base["unmapped_columns"] = []
        base["review_reasons"] = []
        base["missing_required_fields"] = []

    return base
