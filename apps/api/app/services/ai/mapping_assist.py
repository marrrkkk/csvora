from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.models.template import TemplateField
from app.services.ai.openrouter import call_mapping_assist
from app.services.analyzer.template_mapping import TemplateMappingContext, decide_mapping_review_state


def maybe_enhance_analysis_with_ai(
    settings: Settings,
    analysis: dict[str, Any],
    *,
    template_field_keys: list[str],
    template_fields: list[TemplateField],
    ctx: TemplateMappingContext,
    ai_enabled_on_template: bool,
) -> tuple[dict[str, Any], bool]:
    """Mutates mapping-related keys when AI succeeds. Returns (analysis, used_ai)."""
    if not ai_enabled_on_template:
        return analysis, False

    candidates = analysis.get("mapping_candidates") or []
    if not candidates:
        return analysis, False

    system = (
        "You assist CSV column mapping for structured data imports against a developer-defined schema. "
        "You must not invent target_field values outside the allowed list. "
        "You only adjust ranking/confidence/rationale; keep target_field null if unsure. "
        "Output strict JSON object {\"rows\":[{source_column,target_field,confidence,rationale}]}."
    )
    payload = {
        "allowed_target_fields": template_field_keys,
        "deterministic_candidates": candidates,
        "headers": analysis.get("source_columns", []),
    }
    try:
        ai = call_mapping_assist(settings, system_prompt=system, user_payload=payload)
    except Exception:
        return analysis, False
    if ai is None:
        return analysis, False

    by_col = {r.source_column: r for r in ai.rows}
    updated_candidates: list[dict[str, Any]] = []
    for row in candidates:
        col = row.get("source_column")
        adj = by_col.get(col) if isinstance(col, str) else None
        if adj is None:
            updated_candidates.append(row)
            continue
        merged = dict(row)
        if adj.target_field is not None and adj.target_field in template_field_keys:
            merged["target_field"] = adj.target_field
        merged["confidence"] = float(adj.confidence)
        merged["reason"] = "ai_assisted"
        if adj.rationale:
            merged["rationale"] = adj.rationale
        updated_candidates.append(merged)

    assigned: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for m in updated_candidates:
        row = dict(m)
        tgt = row.get("target_field")
        if tgt and tgt in assigned:
            row["target_field"] = None
            row["reason"] = "ai_duplicate_target"
        elif tgt:
            assigned.add(str(tgt))
        deduped.append(row)

    analysis = dict(analysis)
    analysis["mapping_candidates"] = deduped
    analysis["ai_mapping_used"] = True
    columns = list(analysis.get("source_columns") or [])
    decided = decide_mapping_review_state(deduped, columns, ctx, template_fields)
    analysis.update(decided)
    return analysis, True
