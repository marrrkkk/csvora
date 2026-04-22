from pydantic import BaseModel, Field


class AIMappingRow(BaseModel):
    source_column: str = Field(min_length=1, max_length=255)
    target_field: str | None = Field(default=None, max_length=255)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str | None = None


class AIMappingAssistResponse(BaseModel):
    rows: list[AIMappingRow] = Field(default_factory=list)
