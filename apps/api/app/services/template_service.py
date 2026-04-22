from __future__ import annotations



import re

from uuid import UUID



from sqlalchemy import func, select

from sqlalchemy.orm import Session, selectinload



from app.models.enums import TemplateFieldValueType, TemplateStatus

from app.models.template import Template, TemplateField, TemplateVersion

from app.schemas.templates import (

    TemplateCreateRequest,

    TemplateFieldCreate,

    TemplatePatchRequest,

    TemplateVersionCreateRequest,

)





class TemplateService:

    def __init__(self, db: Session) -> None:

        self.db = db



    def get_template_for_owner(self, template_id: UUID, api_key_id: UUID) -> Template | None:

        return self.db.execute(

            select(Template).where(Template.id == template_id, Template.api_key_id == api_key_id)

        ).scalar_one_or_none()



    def list_templates(self, api_key_id: UUID) -> list[Template]:

        return list(

            self.db.scalars(

                select(Template)

                .where(Template.api_key_id == api_key_id)

                .options(selectinload(Template.versions).selectinload(TemplateVersion.fields))

                .order_by(Template.created_at.desc())

            ).all()

        )



    def get_template_detail(self, template_id: UUID, api_key_id: UUID) -> Template | None:

        return self.db.execute(

            select(Template)

            .where(Template.id == template_id, Template.api_key_id == api_key_id)

            .options(selectinload(Template.versions).selectinload(TemplateVersion.fields))

        ).scalar_one_or_none()



    def get_latest_version(self, template_id: UUID) -> TemplateVersion | None:

        return self.db.execute(

            select(TemplateVersion)

            .where(TemplateVersion.template_id == template_id)

            .order_by(TemplateVersion.version.desc())

            .options(selectinload(TemplateVersion.fields))

            .limit(1)

        ).scalar_one_or_none()



    def get_version(self, template_id: UUID, version: int) -> TemplateVersion | None:

        return self.db.execute(

            select(TemplateVersion)

            .where(TemplateVersion.template_id == template_id, TemplateVersion.version == version)

            .options(selectinload(TemplateVersion.fields))

        ).scalar_one_or_none()



    def _validate_fields(self, fields: list[TemplateFieldCreate]) -> None:

        keys = [f.field_key.strip() for f in fields]

        if len(set(keys)) != len(keys):

            raise ValueError("Duplicate field_key in template version")

        for f in fields:

            key = f.field_key.strip()

            if f.value_type is TemplateFieldValueType.ENUM and not (f.enum_values or []):

                raise ValueError(f"enum_values required for ENUM field {key}")



    def create_template(self, api_key_id: UUID, payload: TemplateCreateRequest) -> Template:

        self._validate_fields(payload.version.fields)

        slug_exists = self.db.execute(

            select(func.count()).select_from(Template).where(Template.api_key_id == api_key_id, Template.slug == payload.slug)

        ).scalar_one()

        if int(slug_exists or 0) > 0:

            raise ValueError("slug already exists for this API key")



        template = Template(

            api_key_id=api_key_id,

            name=payload.name.strip(),

            slug=payload.slug.strip().lower(),

            description=payload.description,

            status=payload.status,

            schema_type=payload.schema_type.strip().lower(),

        )

        self.db.add(template)

        self.db.flush()



        tv = TemplateVersion(

            template_id=template.id,

            version=1,

            strict_mode=payload.version.strict_mode,

            auto_accept_confidence=payload.version.auto_accept_confidence,

            review_threshold=payload.version.review_threshold,

            ai_enabled=payload.version.ai_enabled,

            validation_rules=payload.version.validation_rules,

        )

        self.db.add(tv)

        self.db.flush()

        self._persist_fields(tv.id, payload.version.fields)

        self.db.commit()

        self.db.refresh(template)

        return template



    def _persist_fields(self, template_version_id: UUID, fields: list[TemplateFieldCreate]) -> None:

        for f in fields:

            self.db.add(

                TemplateField(

                    template_version_id=template_version_id,

                    field_key=f.field_key.strip(),

                    label=f.label.strip(),

                    value_type=f.value_type,

                    is_builtin=f.is_builtin,

                    is_required=f.is_required,

                    aliases=[a.strip().lower() for a in f.aliases if a and a.strip()],

                    description=f.description,

                    default_value=f.default_value,

                    allow_empty=f.allow_empty,

                    validation_rules=f.validation_rules,

                    normalizer_config=f.normalizer_config,

                    enum_values=f.enum_values,

                    sort_order=f.sort_order,

                )

            )



    def patch_template(self, template_id: UUID, api_key_id: UUID, payload: TemplatePatchRequest) -> Template:

        template = self.get_template_for_owner(template_id, api_key_id)

        if template is None:

            raise LookupError("Template not found")

        if payload.name is not None:

            template.name = payload.name.strip()

        if payload.description is not None:

            template.description = payload.description

        if payload.status is not None:

            template.status = payload.status

        if payload.schema_type is not None:

            template.schema_type = payload.schema_type.strip().lower()

        self.db.add(template)

        self.db.commit()

        self.db.refresh(template)

        return template



    def archive_template(self, template_id: UUID, api_key_id: UUID) -> Template:

        template = self.get_template_for_owner(template_id, api_key_id)

        if template is None:

            raise LookupError("Template not found")

        template.status = TemplateStatus.ARCHIVED

        self.db.add(template)

        self.db.commit()

        self.db.refresh(template)

        return template



    def add_template_version(self, template_id: UUID, api_key_id: UUID, payload: TemplateVersionCreateRequest) -> TemplateVersion:

        template = self.get_template_for_owner(template_id, api_key_id)

        if template is None:

            raise LookupError("Template not found")

        if template.status is TemplateStatus.ARCHIVED:

            raise ValueError("Cannot add versions to an archived template")

        self._validate_fields(payload.fields)

        max_v = self.db.execute(

            select(func.max(TemplateVersion.version)).where(TemplateVersion.template_id == template_id)

        ).scalar_one()

        next_v = int(max_v or 0) + 1

        tv = TemplateVersion(

            template_id=template_id,

            version=next_v,

            strict_mode=payload.strict_mode,

            auto_accept_confidence=payload.auto_accept_confidence,

            review_threshold=payload.review_threshold,

            ai_enabled=payload.ai_enabled,

            validation_rules=payload.validation_rules,

        )

        self.db.add(tv)

        self.db.flush()

        self._persist_fields(tv.id, payload.fields)

        self.db.commit()

        self.db.refresh(tv)

        return tv



    def resolve_version_for_import(self, template_id: UUID, api_key_id: UUID) -> TemplateVersion:

        template = self.get_template_for_owner(template_id, api_key_id)

        if template is None:

            raise LookupError("Template not found")

        if template.status is not TemplateStatus.ACTIVE:

            raise ValueError("Template is not active")

        tv = self.get_latest_version(template_id)

        if tv is None:

            raise ValueError("Template has no versions")

        return tv





def slugify_key_hint(raw: str) -> str:

    s = raw.strip().lower()

    s = re.sub(r"[^a-z0-9]+", "_", s)

    return s.strip("_")

