from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ImportStatus


class ImportRecord(Base):
    __tablename__ = "imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(
            ImportStatus,
            name="import_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=ImportStatus.CREATED,
    )
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_file_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    mappings_finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_mapping_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    template: Mapped["Template | None"] = relationship("Template", foreign_keys=[template_id])
    template_version: Mapped["TemplateVersion | None"] = relationship(
        "TemplateVersion", foreign_keys=[template_version_id]
    )
    mappings: Mapped[list["ImportMapping"]] = relationship(
        back_populates="import_record",
        cascade="all, delete-orphan",
    )
    final_mappings: Mapped[list["ImportFinalMapping"]] = relationship(
        back_populates="import_record",
        cascade="all, delete-orphan",
    )
    mapping_suggestions: Mapped[list["ImportMappingSuggestion"]] = relationship(
        back_populates="import_record",
        cascade="all, delete-orphan",
    )
    errors: Mapped[list["ImportError"]] = relationship(
        back_populates="import_record",
        cascade="all, delete-orphan",
    )
    results: Mapped[list["ImportResult"]] = relationship(
        back_populates="import_record",
        cascade="all, delete-orphan",
    )
    api_key: Mapped["APIKey | None"] = relationship("APIKey", back_populates="imports")
