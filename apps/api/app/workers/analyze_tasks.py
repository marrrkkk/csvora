import json
import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import increment_csvora, increment_task_event, observe_task_duration
from app.db.session import SessionLocal
from app.models.enums import ImportStatus
from app.models.template import Template, TemplateVersion
from app.services.analyzer.file_analyzer import analyze_csv_bytes
from app.services.import_service import ImportService
from app.services.storage.factory import build_storage_service
from app.utils.file_keys import build_analysis_file_key
from app.workers.celery_app import celery_app


@celery_app.task(
    name="imports.analyze",
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_import(import_id: str, request_id: str | None = None) -> dict[str, str]:
    db = SessionLocal()
    structlog.contextvars.clear_contextvars()
    if request_id:
        structlog.contextvars.bind_contextvars(request_id=request_id)
    logger = get_logger().bind(task="imports.analyze", import_id=import_id, request_id=request_id)
    start = time.perf_counter()
    increment_task_event("imports.analyze", "started")
    try:
        service = ImportService(db)
        settings = get_settings()
        storage = build_storage_service(settings)
        import_uuid = UUID(import_id)

        record = service.get_import(import_uuid)
        if record is None:
            raise ValueError("Import not found")
        if record.status in {
            ImportStatus.ANALYZED,
            ImportStatus.NEEDS_REVIEW,
            ImportStatus.READY_TO_TRANSFORM,
            ImportStatus.COMPLETED,
        }:
            increment_task_event("imports.analyze", "skipped")
            logger.info("task_skipped", reason="already_finalized", current_status=record.status.value)
            return {"status": record.status.value, "import_id": import_id}
        if record.status is not ImportStatus.ANALYZING:
            increment_task_event("imports.analyze", "skipped")
            logger.info("task_skipped", reason="not_analyzing", current_status=record.status.value)
            return {"status": record.status.value, "import_id": import_id}
        if not record.source_file_key:
            raise ValueError("Import has no source file")

        template_version: TemplateVersion | None = None
        if record.template_version_id:
            template_version = db.execute(
                select(TemplateVersion)
                .where(TemplateVersion.id == record.template_version_id)
                .options(selectinload(TemplateVersion.fields))
            ).scalar_one_or_none()
            if template_version is None:
                raise ValueError("Import template version not found")

        file_bytes = storage.get_bytes(record.source_file_key)
        analysis = analyze_csv_bytes(
            file_bytes=file_bytes,
            preview_rows=settings.analysis_preview_rows,
            sample_lines=settings.analysis_sample_lines,
            template_version=template_version,
            ai_settings=settings if template_version else None,
        )
        analysis_key = build_analysis_file_key(import_uuid)
        storage.put_bytes(analysis_key, json.dumps(analysis).encode("utf-8"), content_type="application/json")
        saved = service.save_analysis(import_uuid, analysis_key, analysis)
        duration_ms = int((time.perf_counter() - start) * 1000)
        increment_task_event("imports.analyze", "completed")
        observe_task_duration("imports.analyze", duration_ms)
        schema_type_label = ""
        if record.template_id:
            tpl = db.get(Template, record.template_id)
            if tpl is not None:
                schema_type_label = (tpl.schema_type or "").strip().lower()
        increment_csvora(
            "analyze_completed",
            template_id=str(record.template_id or ""),
            template_version_id=str(record.template_version_id or ""),
            used_ai=str(bool(analysis.get("ai_mapping_used"))).lower(),
            requires_review=str(bool(analysis.get("requires_review"))).lower(),
            legacy_mapping=str(bool(analysis.get("legacy_contact_mapping"))).lower(),
            schema_type=schema_type_label,
        )
        logger.info(
            "task_completed",
            duration_ms=duration_ms,
            template_id=str(record.template_id) if record.template_id else None,
            template_version_id=str(record.template_version_id) if record.template_version_id else None,
            requires_review=analysis.get("requires_review"),
            ai_mapping_used=analysis.get("ai_mapping_used"),
        )
        return {"status": saved.status.value, "import_id": import_id}
    except Exception as exc:
        service = ImportService(db)
        service.mark_failed(UUID(import_id), f"Analyze failed: {exc}")
        duration_ms = int((time.perf_counter() - start) * 1000)
        increment_task_event("imports.analyze", "failed")
        observe_task_duration("imports.analyze", duration_ms)
        logger.error("task_failed", error=str(exc), duration_ms=duration_ms)
        raise
    finally:
        structlog.contextvars.clear_contextvars()
        db.close()
