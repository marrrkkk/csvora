from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_api_key_and_rate_limit
from app.models.template import Template
from app.schemas.templates import (
    TemplateCreateRequest,
    TemplatePatchRequest,
    TemplateResponse,
    TemplateVersionCreateRequest,
    TemplateVersionResponse,
)
from app.services.template_service import TemplateService


def _build_version_response(v) -> TemplateVersionResponse:
    return TemplateVersionResponse.model_validate(v)


def _build_template_response(t: Template) -> TemplateResponse:
    versions = sorted(t.versions, key=lambda x: x.version, reverse=True)
    latest = versions[0] if versions else None
    return TemplateResponse(
        id=t.id,
        name=t.name,
        slug=t.slug,
        description=t.description,
        status=t.status,
        schema_type=t.schema_type,
        created_at=t.created_at,
        updated_at=t.updated_at,
        latest_version=_build_version_response(latest) if latest else None,
    )


router = APIRouter(
    prefix="/templates",
    tags=["templates"],
    dependencies=[Depends(require_api_key_and_rate_limit)],
)


def _owner_id_from_request(request: Request) -> UUID:
    raw = getattr(request.state, "api_key_id", None)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authenticated API key context")
    return UUID(str(raw))


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreateRequest, request: Request, db: Session = Depends(get_db)) -> TemplateResponse:
    service = TemplateService(db)
    try:
        t = service.create_template(_owner_id_from_request(request), payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.refresh(t)
    detail = service.get_template_detail(t.id, _owner_id_from_request(request))
    assert detail is not None
    return _build_template_response(detail)


@router.get("", response_model=list[TemplateResponse])
def list_templates(request: Request, db: Session = Depends(get_db)) -> list[TemplateResponse]:
    service = TemplateService(db)
    rows = service.list_templates(_owner_id_from_request(request))
    return [_build_template_response(t) for t in rows]


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: UUID, request: Request, db: Session = Depends(get_db)) -> TemplateResponse:
    service = TemplateService(db)
    t = service.get_template_detail(template_id, _owner_id_from_request(request))
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return _build_template_response(t)


@router.patch("/{template_id}", response_model=TemplateResponse)
def patch_template(
    template_id: UUID,
    payload: TemplatePatchRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TemplateResponse:
    service = TemplateService(db)
    try:
        t = service.patch_template(template_id, _owner_id_from_request(request), payload)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found") from None
    detail = service.get_template_detail(t.id, _owner_id_from_request(request))
    assert detail is not None
    return _build_template_response(detail)


@router.post("/{template_id}/archive", response_model=TemplateResponse)
def archive_template(template_id: UUID, request: Request, db: Session = Depends(get_db)) -> TemplateResponse:
    service = TemplateService(db)
    try:
        t = service.archive_template(template_id, _owner_id_from_request(request))
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found") from None
    detail = service.get_template_detail(t.id, _owner_id_from_request(request))
    assert detail is not None
    return _build_template_response(detail)


@router.post("/{template_id}/versions", response_model=TemplateVersionResponse, status_code=status.HTTP_201_CREATED)
def create_template_version(
    template_id: UUID,
    payload: TemplateVersionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TemplateVersionResponse:
    service = TemplateService(db)
    try:
        v = service.add_template_version(template_id, _owner_id_from_request(request), payload)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _build_version_response(v)
