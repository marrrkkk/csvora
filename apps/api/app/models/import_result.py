from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ImportResult(Base):
    __tablename__ = "import_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("template_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    analysis_used_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cleaned_csv_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    analysis_payload_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    normalized_json_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    validation_report_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    import_record: Mapped["ImportRecord"] = relationship(back_populates="results")
