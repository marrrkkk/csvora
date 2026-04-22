import uuid

import pytest

from app.db.session import SessionLocal
from app.models.enums import ImportStatus
from app.schemas.imports import ImportCreateRequest
from app.services.import_service import ImportService
from app.workers.analyze_tasks import analyze_import
from app.workers.transform_tasks import transform_import


def test_analyze_task_skips_when_not_analyzing() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        rec = service.create_import(ImportCreateRequest(original_filename="a.csv"))
        outcome = analyze_import(str(rec.id))
        assert outcome["status"] == ImportStatus.CREATED.value
    finally:
        db.close()


def test_transform_task_skips_when_not_transforming() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        rec = service.create_import(ImportCreateRequest(original_filename="a.csv"))
        with pytest.raises(Exception):
            transform_import(str(rec.id))
        refreshed = service.get_import(rec.id)
        assert refreshed is not None
        assert refreshed.status == ImportStatus.CREATED
    finally:
        db.close()


def test_mark_failed_ignored_for_completed_state() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        rec = service.create_import(ImportCreateRequest(original_filename="a.csv"))
        rec.status = ImportStatus.COMPLETED
        db.add(rec)
        db.commit()
        changed = service.mark_failed(rec.id, "late fail")
        assert changed is False
    finally:
        db.close()
