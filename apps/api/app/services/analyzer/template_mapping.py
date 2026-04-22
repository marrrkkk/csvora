"""Template-scored column mapping (deterministic; optional AI layer may adjust scores upstream)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from app.models.template import TemplateField, TemplateVersion


@dataclass(frozen=True)
class TemplateMappingContext:
    template_version: TemplateVersion
    auto_accept_confidence: float
    review_threshold: float
    strict_mode: bool


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE)
_PHONE_RE = re.compile(r"[\d+().\-]{7,}")


def _normalize_header(name: str) -> str:
    return name.strip().lower().replace("_", " ")


def _sample_value_hints(values: list[str]) -> set[str]:
    hints: set[str] = set()
    joined = " ".join(v for v in values if v and str(v).strip())
    if not joined:
        return hints
    for v in values[:20]:
        s = str(v).strip()
        if not s:
            continue
        if _EMAIL_RE.search(s):
            hints.add("email")
        if _PHONE_RE.search(s):
            hints.add("phone")
    return hints


def _score_column_to_field(
    column: str,
    field: TemplateField,
    sample_values: list[str],
) -> tuple[float, str]:
    normalized = _normalize_header(column)
    aliases = [a.lower() for a in (field.aliases or []) if isinstance(a, str)]
    field_key_norm = field.field_key.lower().replace("_", " ")
    label_norm = field.label.lower().replace("_", " ")

    if normalized in aliases or normalized == field.field_key.lower():
        return 0.99, "alias_exact"
    if normalized == label_norm:
        return 0.97, "label_exact"

    best = 0.0
    best_reason = "fuzzy"
    for candidate in {field_key_norm, label_norm, *aliases}:
        if not candidate:
            continue
        ratio = SequenceMatcher(None, normalized, candidate).ratio()
        if ratio > best:
            best = ratio
            best_reason = "fuzzy_header"

    hints = _sample_value_hints(sample_values)
    vt = field.value_type.value if hasattr(field.value_type, "value") else str(field.value_type)
    if vt == "email" and "email" in hints:
        best = max(best, 0.92)
        best_reason = "sample_email_type"
    if vt == "phone" and "phone" in hints:
        best = max(best, 0.88)
        best_reason = "sample_phone_type"

    return round(float(best), 5), best_reason


def infer_template_mappings(
    columns: list[str],
    preview_rows: list[dict[str, Any]],
    ctx: TemplateMappingContext,
) -> dict[str, Any]:
    """Return mapping suggestions and review flags for a template-bound import."""
    fields = list(ctx.template_version.fields)
    allowed_keys = {f.field_key for f in fields}
    field_by_key = {f.field_key: f for f in fields}

    column_samples: dict[str, list[str]] = {c: [] for c in columns}
    for row in preview_rows:
        for col in columns:
            val = row.get(col)
            if val is not None and str(val).strip():
                column_samples[col].append(str(val))

    per_column: list[dict[str, Any]] = []
    for column in columns:
        best_field: str | None = None
        best_score = 0.0
        best_reason = "none"
        scores: list[dict[str, Any]] = []
        for fk, field in field_by_key.items():
            sc, reason = _score_column_to_field(column, field, column_samples.get(column, []))
            scores.append({"target_field": fk, "confidence": sc, "reason": reason})
            if sc > best_score:
                best_score = sc
                best_field = fk
                best_reason = reason
        if best_field and best_score >= 0.5:
            per_column.append(
                {
                    "source_column": column,
                    "target_field": best_field,
                    "confidence": best_score,
                    "reason": best_reason,
                    "candidates": sorted(scores, key=lambda x: x["confidence"], reverse=True)[:5],
                }
            )
        else:
            per_column.append(
                {
                    "source_column": column,
                    "target_field": None,
                    "confidence": best_score,
                    "reason": "no_match",
                    "candidates": sorted(scores, key=lambda x: x["confidence"], reverse=True)[:5],
                }
            )

    # Greedy one-to-one assignment by descending confidence
    sorted_idx = sorted(
        range(len(per_column)),
        key=lambda i: float(per_column[i].get("confidence") or 0.0),
        reverse=True,
    )
    assigned_targets: set[str] = set()
    final_mappings: list[dict[str, Any]] = []
    for i in sorted_idx:
        row = per_column[i]
        col = row["source_column"]
        tgt = row.get("target_field")
        conf = float(row.get("confidence") or 0.0)
        if tgt is None or tgt in assigned_targets:
            final_mappings.append(
                {
                    "source_column": col,
                    "target_field": None,
                    "confidence": conf,
                    "reason": "unmapped_or_duplicate",
                    "candidates": row.get("candidates", []),
                }
            )
            continue
        assigned_targets.add(tgt)
        final_mappings.append(
            {
                "source_column": col,
                "target_field": tgt,
                "confidence": conf,
                "reason": row.get("reason", "fuzzy"),
                "candidates": row.get("candidates", []),
            }
        )

    final_mappings.sort(key=lambda r: columns.index(r["source_column"]) if r["source_column"] in columns else 999)

    return decide_mapping_review_state(final_mappings, columns, ctx, fields)


def decide_mapping_review_state(
    final_mappings: list[dict[str, Any]],
    columns: list[str],
    ctx: TemplateMappingContext,
    fields: list[TemplateField],
) -> dict[str, Any]:
    auto_accept = float(ctx.auto_accept_confidence)
    review_line = float(ctx.review_threshold)

    auto_approved: list[dict[str, Any]] = []
    needs_review_reasons: list[str] = []
    for m in final_mappings:
        tgt = m.get("target_field")
        conf = float(m.get("confidence") or 0.0)
        if tgt is None:
            needs_review_reasons.append(f"unmapped_column:{m['source_column']}")
            continue
        if conf >= auto_accept:
            auto_approved.append(
                {
                    "source_column": m["source_column"],
                    "target_field": tgt,
                    "confidence": conf,
                    "reason": m.get("reason"),
                }
            )
        elif conf >= review_line:
            needs_review_reasons.append(f"ambiguous:{m['source_column']}->{tgt}:{conf}")
        else:
            needs_review_reasons.append(f"low_confidence:{m['source_column']}->{tgt}:{conf}")

    required_keys = {f.field_key for f in fields if f.is_required}
    covered = {m["target_field"] for m in auto_approved if m.get("target_field")}
    missing_required = sorted(required_keys - covered)
    for mk in missing_required:
        needs_review_reasons.append(f"missing_required_target:{mk}")

    unmapped_columns = [m["source_column"] for m in final_mappings if m.get("target_field") is None]

    strict_extra = ctx.strict_mode and bool(unmapped_columns)

    requires_review = bool(needs_review_reasons or missing_required or strict_extra)

    return {
        "mapping_suggestions": [
            {k: v for k, v in m.items() if k != "candidates"}
            for m in final_mappings
        ],
        "mapping_candidates": final_mappings,
        "auto_approved_mappings": auto_approved,
        "requires_review": requires_review,
        "unmapped_columns": unmapped_columns,
        "review_reasons": needs_review_reasons,
        "missing_required_fields": missing_required,
    }
