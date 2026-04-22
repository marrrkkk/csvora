from app.schemas.imports import ImportCreateRequest
from app.services.import_service import ImportService
from app.db.session import SessionLocal
from sqlalchemy import text


def test_import_result_unique_per_import() -> None:
    db = SessionLocal()
    try:
        service = ImportService(db)
        record = service.create_import(ImportCreateRequest(original_filename="foo.csv"))
        service.save_analysis(record.id, "analysis-key-1", {"mapping_suggestions": []})
        service.save_analysis(record.id, "analysis-key-2", {"mapping_suggestions": []})
        count = db.execute(
            text("select count(*) from import_results where import_id = :import_id"),
            {"import_id": str(record.id)},
        ).scalar_one()
        assert count == 1
    finally:
        db.close()
