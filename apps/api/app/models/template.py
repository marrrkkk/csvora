from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TemplateFieldValueType, TemplateStatus

_enum_kwargs = dict(
    native_enum=False,
    values_callable=lambda cls: [i.value for i in cls],
)


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("api_key_id", "slug", name="uq_templates_api_key_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TemplateStatus] = mapped_column(
        SAEnum(TemplateStatus, name="template_status", **_enum_kwargs),
        nullable=False,
        default=TemplateStatus.ACTIVE,
    )
    schema_type: Mapped[str] = mapped_column(String(128), nullable=False, default="contacts")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateVersion.version",
    )
    api_key: Mapped["APIKey"] = relationship("APIKey", back_populates="templates")


class TemplateVersion(Base):
    __tablename__ = "template_versions"
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_template_versions_template_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    strict_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_accept_confidence: Mapped[float] = mapped_column(Numeric(6, 5), nullable=False, default=0.9)
    review_threshold: Mapped[float] = mapped_column(Numeric(6, 5), nullable=False, default=0.75)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    template: Mapped["Template"] = relationship(back_populates="versions")
    fields: Mapped[list["TemplateField"]] = relationship(
        back_populates="template_version",
        cascade="all, delete-orphan",
        order_by="TemplateField.sort_order",
    )


class TemplateField(Base):
    __tablename__ = "template_fields"
    __table_args__ = (UniqueConstraint("template_version_id", "field_key", name="uq_template_fields_version_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value_type: Mapped[TemplateFieldValueType] = mapped_column(
        SAEnum(TemplateFieldValueType, name="template_field_value_type", **_enum_kwargs),
        nullable=False,
    )
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aliases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_value: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    allow_empty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    validation_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    normalizer_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    enum_values: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    template_version: Mapped["TemplateVersion"] = relationship(back_populates="fields")
