from app.db.session import SessionLocal
from app.models.enums import ImportStatus
from app.schemas.transform import MappingApprovalItem
from app.schemas.imports import ImportCreateRequest
from app.services.import_service import ImportService


def test_mark_failed_does_not_regress_completed() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        record = service.create_import(ImportCreateRequest(original_filename=None))
        record.status = ImportStatus.COMPLETED
        db.add(record)
        db.commit()

        changed = service.mark_failed(record.id, "late failure")
        assert changed is False

        refreshed = service.get_import(record.id)
        assert refreshed is not None
        assert refreshed.status == ImportStatus.COMPLETED
    finally:
        db.close()


def test_start_analyze_if_ready_only_once() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        record = service.create_import(ImportCreateRequest(original_filename="a.csv"))
        record.status = ImportStatus.UPLOADED
        db.add(record)
        db.commit()

        first = service.start_analyze_if_ready(record.id)
        second = service.start_analyze_if_ready(record.id)
        assert first is True
        assert second is False
    finally:
        db.close()


def test_start_transform_if_ready_only_once() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        record = service.create_import(ImportCreateRequest(original_filename="a.csv"))
        record.status = ImportStatus.ANALYZED
        db.add(record)
        db.commit()
        mappings = [MappingApprovalItem(source_column="email", target_field="email")]

        first = service.start_transform_if_ready(record.id, mappings)
        second = service.start_transform_if_ready(record.id, mappings)
        assert first is True
        assert second is False
    finally:
        db.close()

