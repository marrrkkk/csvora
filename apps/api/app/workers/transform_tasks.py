import csv
import io
import json
import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import increment_csvora, increment_task_event, observe_task_duration
from app.db.session import SessionLocal
from app.models.enums import ImportStatus
from app.models.template import TemplateVersion
from app.services.import_service import ImportService
from app.services.storage.factory import build_storage_service
from app.services.transform.transformer import CANONICAL_FIELDS, run_transform
from app.utils.file_keys import build_output_file_keys
from app.workers.celery_app import celery_app


@celery_app.task(
    name="imports.transform",
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def transform_import(import_id: str, request_id: str | None = None) -> dict[str, str]:
    db = SessionLocal()
    structlog.contextvars.clear_contextvars()
    if request_id:
        structlog.contextvars.bind_contextvars(request_id=request_id)
    logger = get_logger().bind(task="imports.transform", import_id=import_id, request_id=request_id)
    start = time.perf_counter()
    increment_task_event("imports.transform", "started")
    try:
        service = ImportService(db)
        settings = get_settings()
        storage = build_storage_service(settings)
        import_uuid = UUID(import_id)

        record = service.get_import(import_uuid)
        if record is None or not record.source_file_key:
            raise ValueError("Import missing source file")
        if record.status is ImportStatus.COMPLETED:
            increment_task_event("imports.transform", "skipped")
            logger.info("task_skipped", reason="already_completed")
            return {"status": "completed", "import_id": import_id}
        if record.status is not ImportStatus.TRANSFORMING:
            increment_task_event("imports.transform", "skipped")
            logger.info("task_skipped", reason="not_transforming", current_status=record.status.value)
            return {"status": record.status.value, "import_id": import_id}

        mappings = service.get_mappings_for_import(import_uuid)
        if not mappings:
            raise ValueError("No mappings available for transform")

        source_bytes = storage.get_bytes(record.source_file_key)

        fields_by_key = None
        template_validation_rules: dict | None = None
        schema_type_label = ""
        if record.template_version_id:
            tv = (
                db.execute(
                    select(TemplateVersion)
                    .where(TemplateVersion.id == record.template_version_id)
                    .options(selectinload(TemplateVersion.fields), joinedload(TemplateVersion.template))
                )
                .unique()
                .scalar_one_or_none()
            )
            if tv is not None:
                fields_by_key = {f.field_key: f for f in tv.fields}
                template_validation_rules = tv.validation_rules
                if tv.template is not None:
                    schema_type_label = (tv.template.schema_type or "").strip().lower()
                    if (
                        template_validation_rules is None
                        and schema_type_label == "contacts"
                        and "email" in fields_by_key
                        and "phone" in fields_by_key
                    ):
                        template_validation_rules = {"require_one_of": [["email", "phone"]]}

        transform_result = run_transform(
            source_bytes,
            mappings,
            fields_by_key=fields_by_key,
            template_validation_rules=template_validation_rules,
        )

        keys = build_output_file_keys(import_uuid)
        cleaned_rows = transform_result["cleaned_rows"]
        normalized_rows = transform_result["normalized_rows"]
        issues = transform_result["issues"]
        fieldnames = transform_result.get("output_fieldnames") or list(CANONICAL_FIELDS)
        if settings.transform_phone_warning_is_error:
            upgraded: list[dict[str, object]] = []
            for issue in issues:
                if issue.get("field_name") == "phone" and issue.get("severity") == "warning":
                    issue = {**issue, "severity": "error", "message": issue.get("message", "Phone format unusual")}
                upgraded.append(issue)
            issues = upgraded
        invalid_count = int(
            transform_result["invalid_row_count"]
            + sum(1 for issue in issues if issue.get("severity") == "error" and issue.get("field_name") == "phone")
        )

        # cleaned csv
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in cleaned_rows:
            csv_row: dict[str, object] = {}
            for k in fieldnames:
                v = row.get(k)
                if isinstance(v, list):
                    csv_row[k] = ";".join(str(x) for x in v)
                elif hasattr(v, "isoformat"):
                    csv_row[k] = v.isoformat()
                elif isinstance(v, bool):
                    csv_row[k] = str(v).lower()
                else:
                    csv_row[k] = v
            writer.writerow({k: csv_row.get(k) for k in fieldnames})

        storage.put_bytes(keys["cleaned_csv_key"], csv_buffer.getvalue().encode("utf-8"), content_type="text/csv")
        storage.put_bytes(
            keys["normalized_json_key"],
            json.dumps(normalized_rows).encode("utf-8"),
            content_type="application/json",
        )
        storage.put_bytes(
            keys["validation_report_key"],
            json.dumps({"issues": issues}).encode("utf-8"),
            content_type="application/json",
        )

        service.save_transform_result(
            import_id=import_uuid,
            valid_row_count=int(transform_result["valid_row_count"]),
            invalid_row_count=invalid_count,
            cleaned_csv_key=keys["cleaned_csv_key"],
            normalized_json_key=keys["normalized_json_key"],
            validation_report_key=keys["validation_report_key"],
            issues=issues,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        increment_task_event("imports.transform", "completed")
        observe_task_duration("imports.transform", duration_ms)
        increment_csvora(
            "transform_completed",
            template_id=str(record.template_id or ""),
            template_version_id=str(record.template_version_id or ""),
            schema_type=schema_type_label,
        )
        logger.info(
            "task_completed",
            duration_ms=duration_ms,
            template_id=str(record.template_id) if record.template_id else None,
            template_version_id=str(record.template_version_id) if record.template_version_id else None,
        )
        return {"status": "completed", "import_id": import_id}
    except Exception as exc:
        service = ImportService(db)
        service.mark_failed(UUID(import_id), f"Transform failed: {exc}")
        duration_ms = int((time.perf_counter() - start) * 1000)
        increment_task_event("imports.transform", "failed")
        observe_task_duration("imports.transform", duration_ms)
        logger.error("task_failed", error=str(exc), duration_ms=duration_ms)
        raise
    finally:
        structlog.contextvars.clear_contextvars()
        db.close()
