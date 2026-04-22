from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import TemplateFieldValueType, TemplateStatus

_SCHEMA_TYPE_PATTERN = r"^[a-z0-9][a-z0-9_-]*$"


class TemplateFieldCreate(BaseModel):
    field_key: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=255)
    value_type: TemplateFieldValueType
    is_builtin: bool = False
    is_required: bool = False
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    default_value: Any | None = None
    allow_empty: bool = True
    validation_rules: dict[str, Any] | None = None
    normalizer_config: dict[str, Any] | None = None
    enum_values: list[Any] | None = None
    sort_order: int = 0


class TemplateVersionCreate(BaseModel):
    strict_mode: bool = True
    auto_accept_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    ai_enabled: bool = False
    validation_rules: dict[str, Any] | None = None
    fields: list[TemplateFieldCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_thresholds(self) -> TemplateVersionCreate:
        if self.review_threshold > self.auto_accept_confidence:
            raise ValueError("review_threshold must be <= auto_accept_confidence")
        return self


class TemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    description: str | None = None
    schema_type: str = Field(default="contacts", max_length=128, pattern=_SCHEMA_TYPE_PATTERN)
    status: TemplateStatus = TemplateStatus.ACTIVE
    version: TemplateVersionCreate


class TemplatePatchRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TemplateStatus | None = None
    schema_type: str | None = Field(default=None, max_length=128, pattern=_SCHEMA_TYPE_PATTERN)


class TemplateFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field_key: str
    label: str
    value_type: TemplateFieldValueType
    is_builtin: bool
    is_required: bool
    aliases: list[str]
    description: str | None
    default_value: Any | None
    allow_empty: bool
    validation_rules: dict[str, Any] | None
    normalizer_config: dict[str, Any] | None
    enum_values: list[Any] | None
    sort_order: int

    @field_validator("aliases", mode="before")
    @classmethod
    def coerce_aliases(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    strict_mode: bool
    auto_accept_confidence: float
    review_threshold: float
    ai_enabled: bool
    validation_rules: dict[str, Any] | None = None
    created_at: datetime
    fields: list[TemplateFieldResponse]


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    status: TemplateStatus
    schema_type: str
    created_at: datetime
    updated_at: datetime
    latest_version: TemplateVersionResponse | None = None


class TemplateVersionCreateRequest(BaseModel):
    """Publish a new immutable template version."""

    strict_mode: bool = True
    auto_accept_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    ai_enabled: bool = False
    validation_rules: dict[str, Any] | None = None
    fields: list[TemplateFieldCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_thresholds(self) -> TemplateVersionCreateRequest:
        if self.review_threshold > self.auto_accept_confidence:
            raise ValueError("review_threshold must be <= auto_accept_confidence")
        return self
