from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_storage_service, require_api_key_and_rate_limit
from app.core.config import get_settings
from app.core.metrics import increment_csvora
from app.models.enums import ImportStatus
from app.schemas.analysis import AnalyzeTriggerResponse, ImportAnalysisResponse, ImportStatusResponse
from app.schemas.imports import ApproveMappingsRequest, ImportCreateRequest, ImportResponse
from app.schemas.transform import TransformRequest, TransformResultResponse, TransformTriggerResponse, RowIssue
from app.models.template import Template
from app.services.import_service import ImportService
from app.services.storage.base import StorageService
from app.workers.analyze_tasks import analyze_import
from app.workers.celery_app import celery_app
from app.workers.transform_tasks import transform_import

router = APIRouter(
    prefix="/imports",
    tags=["imports"],
    dependencies=[Depends(require_api_key_and_rate_limit)],
)


def _owner_id_from_request(request: Request) -> UUID:
    raw = getattr(request.state, "api_key_id", None)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authenticated API key context")
    return UUID(str(raw))


@router.post("", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
def create_import(payload: ImportCreateRequest, request: Request, db: Session = Depends(get_db)) -> ImportResponse:
    service = ImportService(db)
    settings = get_settings()
    try:
        record = service.create_import(
            payload,
            api_key_id=_owner_id_from_request(request),
            require_template=settings.import_requires_template,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ImportResponse.model_validate(record)


@router.post("/{import_id}/analyze", response_model=AnalyzeTriggerResponse)
def trigger_import_analyze(
    import_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> AnalyzeTriggerResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    if not record.source_file_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Import has no uploaded source file")
    if record.status is ImportStatus.ANALYZING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analyze job already in progress")
    if record.status is not ImportStatus.UPLOADED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Import is not ready for analysis")

    started = service.start_analyze_if_ready(import_id)
    if not started:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analyze job already in progress")
    rid = getattr(request.state, "request_id", None)
    if celery_app.conf.task_always_eager:
        analyze_import.apply(args=(str(import_id),), kwargs={"request_id": rid}, throw=False)
    else:
        analyze_import.delay(str(import_id), request_id=rid)
    return AnalyzeTriggerResponse(import_id=import_id, status=ImportStatus.ANALYZING, message="Analyze job queued")


@router.get("/{import_id}/status", response_model=ImportStatusResponse)
def get_import_status(import_id: UUID, request: Request, db: Session = Depends(get_db)) -> ImportStatusResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    return ImportStatusResponse(
        import_id=record.id,
        status=record.status,
        updated_at=record.updated_at,
        template_id=record.template_id,
        template_version_id=record.template_version_id,
        mappings_finalized_at=record.mappings_finalized_at,
        final_mapping_revision=record.final_mapping_revision,
    )


@router.get("/{import_id}/analysis", response_model=ImportAnalysisResponse)
def get_import_analysis(
    import_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> ImportAnalysisResponse:
    import json

    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

    analysis_key = service.get_analysis_payload_key(import_id)
    if not analysis_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis result not found")

    payload = json.loads(storage.get_bytes(analysis_key).decode("utf-8"))
    return ImportAnalysisResponse.model_validate({"import_id": import_id, **payload})


@router.post("/{import_id}/approve-mappings", response_model=ImportResponse)
def approve_import_mappings(
    import_id: UUID,
    payload: ApproveMappingsRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ImportResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    if record.status is not ImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Import is not waiting for mapping approval",
        )
    try:
        record = service.save_approved_mappings(import_id, payload.mappings)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    tpl = db.get(Template, record.template_id) if record.template_id else None
    schema_type_label = (tpl.schema_type or "").strip().lower() if tpl else ""
    increment_csvora(
        "mappings_approved",
        template_id=str(record.template_id or ""),
        template_version_id=str(record.template_version_id or ""),
        schema_type=schema_type_label,
    )
    return ImportResponse.model_validate(record)


@router.post("/{import_id}/transform", response_model=TransformTriggerResponse)
def trigger_import_transform(
    import_id: UUID,
    payload: TransformRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TransformTriggerResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    if record.status is ImportStatus.TRANSFORMING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transform job already in progress")
    if record.status is ImportStatus.NEEDS_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Import requires approved mappings before transform",
        )
    if record.status not in {ImportStatus.ANALYZED, ImportStatus.READY_TO_TRANSFORM}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Import is not ready for transform")
    if record.status is ImportStatus.ANALYZED and not (payload.mappings or []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mappings are required for this import")

    started = service.start_transform_if_ready(import_id, payload.mappings)
    if not started:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transform job already in progress")
    rec = service.get_import(import_id)
    if rec:
        tpl = db.get(Template, rec.template_id) if rec.template_id else None
        schema_type_label = (tpl.schema_type or "").strip().lower() if tpl else ""
        increment_csvora(
            "transform_queued",
            template_id=str(rec.template_id or ""),
            template_version_id=str(rec.template_version_id or ""),
            schema_type=schema_type_label,
        )
    rid = getattr(request.state, "request_id", None)
    if celery_app.conf.task_always_eager:
        transform_import.apply(args=(str(import_id),), kwargs={"request_id": rid}, throw=False)
    else:
        transform_import.delay(str(import_id), request_id=rid)
    return TransformTriggerResponse(import_id=import_id, status=ImportStatus.TRANSFORMING, message="Transform job queued")


@router.get("/{import_id}/result", response_model=TransformResultResponse)
def get_import_result(import_id: UUID, request: Request, db: Session = Depends(get_db)) -> TransformResultResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

    result, issues = service.get_result(import_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transform result not found")

    return TransformResultResponse(
        import_id=import_id,
        status=record.status,
        valid_row_count=result.valid_row_count,
        invalid_row_count=result.invalid_row_count,
        cleaned_csv_key=result.cleaned_csv_key,
        normalized_json_key=result.normalized_json_key,
        validation_report_key=result.validation_report_key,
        issues=[
            RowIssue(
                row_number=issue.row_number,
                field_name=issue.field_name,
                severity=issue.severity,
                message=issue.message,
            )
            for issue in issues
        ],
        updated_at=record.updated_at,
    )


@router.get("/{import_id}", response_model=ImportResponse)
def get_import(import_id: UUID, request: Request, db: Session = Depends(get_db)) -> ImportResponse:
    service = ImportService(db)
    record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    return ImportResponse.model_validate(record)


@router.post("/{import_id}/upload", response_model=ImportResponse)
async def upload_import_file(
    import_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> ImportResponse:
    settings = get_settings()
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")
    if file.content_type not in {None, "", "text/csv", "application/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file content type")

    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > settings.max_upload_size_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
        chunks.append(chunk)
    payload = b"".join(chunks)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if b"\n" not in payload and b"\r" not in payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV content")

    service = ImportService(db)
    try:
        record = service.get_import_for_owner(import_id, _owner_id_from_request(request))
        if record is None:
            raise LookupError("Import not found")
        record = service.upload_source_file(
            import_id=import_id,
            filename=filename,
            file_bytes=payload,
            storage=storage,
            content_type=file.content_type,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ImportResponse.model_validate(record)
