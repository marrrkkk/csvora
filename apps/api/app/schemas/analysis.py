from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus


class AnalyzeTriggerResponse(BaseModel):
    import_id: UUID
    status: ImportStatus
    message: str


class ImportStatusResponse(BaseModel):
    import_id: UUID
    status: ImportStatus
    updated_at: datetime
    template_id: UUID | None = None
    template_version_id: UUID | None = None
    mappings_finalized_at: datetime | None = None
    final_mapping_revision: int = 0


class ImportAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    import_id: UUID
    delimiter: str | None = None
    encoding: str | None = None
    header_row_index: int | None = None
    total_rows: int | None = None
    source_columns: list[str] | None = None
    mapping_suggestions: list[dict[str, object]] | None = None
    preview_rows: list[dict[str, object]] | None = None
    warnings: list[str] | None = None
    requires_review: bool | None = None
    auto_approved_mappings: list[dict[str, object]] | None = None
    unmapped_columns: list[str] | None = None
    review_reasons: list[str] | None = None
    missing_required_fields: list[str] | None = None
    mapping_candidates: list[dict[str, object]] | None = None
    template_version_id: str | None = None
    ai_mapping_used: bool | None = None
