from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus
from app.schemas.transform import MappingApprovalItem


class ImportCreateRequest(BaseModel):
    original_filename: str | None = None
    template_id: UUID | None = None


class ImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ImportStatus
    original_filename: str | None
    source_file_key: str | None
    template_id: UUID | None = None
    template_version_id: UUID | None = None
    mappings_finalized_at: datetime | None = None
    final_mapping_revision: int = 0
    created_at: datetime
    updated_at: datetime


class ApproveMappingsRequest(BaseModel):
    mappings: list[MappingApprovalItem]
