from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ImportStatus

IssueSeverity = Literal["error", "warning"]


class MappingApprovalItem(BaseModel):
    source_column: str = Field(min_length=1, max_length=255)
    target_field: str = Field(min_length=1, max_length=255)


class TransformRequest(BaseModel):
    mappings: list[MappingApprovalItem] | None = None

    @model_validator(mode="after")
    def validate_unique_mappings(self) -> "TransformRequest":
        mappings = self.mappings
        if mappings is None:
            return self
        if not mappings:
            raise ValueError("When provided, mappings must not be empty")

        source_columns = [item.source_column.strip() for item in mappings]
        target_fields = [item.target_field.strip() for item in mappings]
        if len(set(source_columns)) != len(source_columns):
            raise ValueError("Duplicate source_column values are not allowed")
        if len(set(target_fields)) != len(target_fields):
            raise ValueError("Duplicate target_field values are not allowed")
        return self


class TransformTriggerResponse(BaseModel):
    import_id: UUID
    status: ImportStatus
    message: str


class RowIssue(BaseModel):
    row_number: int | None
    field_name: str | None
    severity: IssueSeverity
    message: str


class TransformResultResponse(BaseModel):
    import_id: UUID
    status: ImportStatus
    valid_row_count: int
    invalid_row_count: int
    cleaned_csv_key: str | None
    normalized_json_key: str | None
    validation_report_key: str | None
    issues: list[RowIssue]
    updated_at: datetime
