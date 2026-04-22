from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import ImportStatus
from app.models.import_error import ImportError
from app.models.import_final_mapping import ImportFinalMapping
from app.models.import_mapping import ImportMapping
from app.models.import_mapping_suggestion import ImportMappingSuggestion
from app.models.import_record import ImportRecord
from app.models.import_result import ImportResult
from app.models.template import TemplateVersion
from app.schemas.imports import ImportCreateRequest
from app.schemas.transform import MappingApprovalItem
from app.services.storage.base import StorageService
from app.services.template_service import TemplateService
from app.utils.file_keys import build_source_file_key


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _snapshot_final_mappings(self, record: ImportRecord) -> None:
        if not record.template_version_id:
            return
        rows = self.db.execute(select(ImportMapping).where(ImportMapping.import_id == record.id)).scalars().all()
        if not rows:
            return
        record.final_mapping_revision = int(record.final_mapping_revision or 0) + 1
        record.mappings_finalized_at = datetime.now(timezone.utc)
        for r in rows:
            self.db.add(
                ImportFinalMapping(
                    import_id=record.id,
                    template_version_id=record.template_version_id,
                    revision=record.final_mapping_revision,
                    source_column=r.source_column,
                    target_field=r.target_field,
                    confidence_score=float(r.confidence_score) if r.confidence_score is not None else None,
                )
            )

    def create_import(
        self,
        payload: ImportCreateRequest,
        api_key_id: UUID | None = None,
        *,
        require_template: bool = False,
    ) -> ImportRecord:
        if require_template and payload.template_id is None:
            raise ValueError("template_id is required for imports in this environment")
        template_id = payload.template_id
        template_version_id: UUID | None = None
        resolved_template_id: UUID | None = None
        if template_id is not None:
            if api_key_id is None:
                raise ValueError("template_id requires an authenticated API key")
            ts = TemplateService(self.db)
            tv = ts.resolve_version_for_import(template_id, api_key_id)
            template_version_id = tv.id
            resolved_template_id = template_id

        record = ImportRecord(
            status=ImportStatus.CREATED,
            original_filename=payload.original_filename,
            api_key_id=api_key_id,
            template_id=resolved_template_id,
            template_version_id=template_version_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_import(self, import_id: UUID) -> ImportRecord | None:
        return self.db.get(ImportRecord, import_id)

    def get_import_for_owner(self, import_id: UUID, api_key_id: UUID) -> ImportRecord | None:
        return self.db.execute(
            select(ImportRecord).where(
                ImportRecord.id == import_id,
                ImportRecord.api_key_id == api_key_id,
            )
        ).scalar_one_or_none()

    def upload_source_file(
        self,
        import_id: UUID,
        filename: str,
        file_bytes: bytes,
        storage: StorageService,
        content_type: str | None = None,
    ) -> ImportRecord:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")

        if record.status not in {ImportStatus.CREATED, ImportStatus.UPLOADED}:
            raise ValueError("Import is not in a valid state for upload")

        source_key = build_source_file_key(import_id=record.id, filename=filename)
        storage.put_bytes(key=source_key, data=file_bytes, content_type=content_type)

        record.original_filename = filename
        record.source_file_key = source_key
        record.status = ImportStatus.UPLOADED
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_analyzing(self, import_id: UUID) -> ImportRecord:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")
        if record.status is not ImportStatus.UPLOADED:
            raise ValueError("Import is not ready for analysis")
        record.status = ImportStatus.ANALYZING
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def start_analyze_if_ready(self, import_id: UUID) -> bool:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")
        if record.status is not ImportStatus.UPLOADED:
            return False
        record.status = ImportStatus.ANALYZING
        self.db.add(record)
        self.db.commit()
        return True

    def mark_failed(self, import_id: UUID, message: str) -> bool:
        record = self.get_import(import_id)
        if record is None:
            return False
        if record.status not in {ImportStatus.ANALYZING, ImportStatus.TRANSFORMING}:
            return False
        record.status = ImportStatus.FAILED
        self.db.add(record)
        self.db.add(ImportError(import_id=record.id, row_number=None, field_name=None, severity="error", message=message))
        self.db.commit()
        return True

    def save_analysis(
        self,
        import_id: UUID,
        analysis_payload_key: str,
        analysis_payload: dict[str, object],
    ) -> ImportRecord:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")

        self.db.query(ImportMappingSuggestion).filter(ImportMappingSuggestion.import_id == record.id).delete()
        self.db.query(ImportMapping).filter(ImportMapping.import_id == record.id).delete()

        candidates = analysis_payload.get("mapping_candidates")
        if not candidates and analysis_payload.get("mapping_suggestions"):
            candidates = [
                {
                    "source_column": s["source_column"],
                    "target_field": s.get("target_field"),
                    "confidence": s.get("confidence"),
                    "reason": s.get("reason"),
                    "rationale": None,
                    "candidates": [],
                }
                for s in analysis_payload["mapping_suggestions"]
            ]

        auto_pairs = {
            (str(m["source_column"]), str(m["target_field"]))
            for m in (analysis_payload.get("auto_approved_mappings") or [])
            if m.get("target_field")
        }

        for row in candidates or []:
            src = str(row["source_column"])
            tgt = row.get("target_field")
            tgt_s = str(tgt) if tgt is not None else None
            conf = row.get("confidence")
            auto_accepted = (src, tgt_s) in auto_pairs if tgt_s else False
            self.db.add(
                ImportMappingSuggestion(
                    import_id=record.id,
                    source_column=src,
                    target_field=tgt_s,
                    confidence_score=float(conf) if conf is not None else None,
                    reason=str(row["reason"])[:64] if row.get("reason") else None,
                    rationale=str(row["rationale"])[:4000] if row.get("rationale") else None,
                    auto_accepted=auto_accepted,
                )
            )

        result = (
            self.db.execute(select(ImportResult).where(ImportResult.import_id == record.id)).scalar_one_or_none()
        )
        if result is None:
            result = ImportResult(import_id=record.id)
        result.analysis_payload_key = analysis_payload_key
        result.analysis_used_ai = bool(analysis_payload.get("ai_mapping_used"))
        if record.template_version_id:
            result.template_version_id = record.template_version_id
        self.db.add(result)

        if record.template_version_id:
            requires_review = bool(analysis_payload.get("requires_review"))
            if requires_review:
                record.status = ImportStatus.NEEDS_REVIEW
            else:
                record.status = ImportStatus.READY_TO_TRANSFORM
                for m in analysis_payload.get("auto_approved_mappings") or []:
                    if not m.get("target_field"):
                        continue
                    self.db.add(
                        ImportMapping(
                            import_id=record.id,
                            source_column=str(m["source_column"]),
                            target_field=str(m["target_field"]),
                            confidence_score=float(m.get("confidence") or 1.0),
                        )
                    )
                self._snapshot_final_mappings(record)
        else:
            record.status = ImportStatus.ANALYZED

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_analysis_payload_key(self, import_id: UUID) -> str | None:
        result = self.db.execute(select(ImportResult).where(ImportResult.import_id == import_id)).scalar_one_or_none()
        if result is None:
            return None
        return result.analysis_payload_key

    def mark_transforming(self, import_id: UUID, mappings: list[MappingApprovalItem]) -> ImportRecord:
        started = self.start_transform_if_ready(import_id, mappings)
        if not started:
            raise ValueError("Import is not ready for transform")
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")
        return record

    def start_transform_if_ready(self, import_id: UUID, mappings: list[MappingApprovalItem] | None) -> bool:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")

        if record.status is ImportStatus.READY_TO_TRANSFORM:
            effective = list(mappings or [])
            if not effective:
                rows = self.db.execute(select(ImportMapping).where(ImportMapping.import_id == import_id)).scalars().all()
                effective = [
                    MappingApprovalItem(source_column=r.source_column, target_field=r.target_field)
                    for r in rows
                    if r.target_field
                ]
            if not effective:
                return False
            self.db.query(ImportMapping).filter(ImportMapping.import_id == record.id).delete()
            for item in effective:
                self.db.add(
                    ImportMapping(
                        import_id=record.id,
                        source_column=item.source_column,
                        target_field=item.target_field,
                        confidence_score=1.0,
                    )
                )
            record.status = ImportStatus.TRANSFORMING
            self.db.add(record)
            self.db.commit()
            return True

        if record.status is ImportStatus.ANALYZED:
            if not mappings:
                return False
            self.db.query(ImportMapping).filter(ImportMapping.import_id == record.id).delete()
            for item in mappings:
                self.db.add(
                    ImportMapping(
                        import_id=record.id,
                        source_column=item.source_column,
                        target_field=item.target_field,
                        confidence_score=1.0,
                    )
                )
            record.status = ImportStatus.TRANSFORMING
            self.db.add(record)
            self.db.commit()
            return True

        return False

    def save_approved_mappings(self, import_id: UUID, mappings: list[MappingApprovalItem]) -> ImportRecord:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")
        if record.status is not ImportStatus.NEEDS_REVIEW:
            raise ValueError("Import is not waiting for mapping review")

        allowed: set[str] | None = None
        if record.template_version_id:
            tv = self.db.execute(
                select(TemplateVersion)
                .where(TemplateVersion.id == record.template_version_id)
                .options(selectinload(TemplateVersion.fields))
            ).scalar_one_or_none()
            if tv is None:
                raise ValueError("Template version not found for import")
            allowed = {f.field_key for f in tv.fields}

        sources = [m.source_column.strip() for m in mappings]
        targets = [m.target_field.strip() for m in mappings]
        if len(set(sources)) != len(sources):
            raise ValueError("Duplicate source_column values are not allowed")
        if len(set(targets)) != len(targets):
            raise ValueError("Duplicate target_field values are not allowed")
        for m in mappings:
            if allowed is not None and m.target_field not in allowed:
                raise ValueError(f"Unknown target_field for template: {m.target_field}")

        self.db.query(ImportMapping).filter(ImportMapping.import_id == record.id).delete()
        for item in mappings:
            self.db.add(
                ImportMapping(
                    import_id=record.id,
                    source_column=item.source_column,
                    target_field=item.target_field,
                    confidence_score=1.0,
                )
            )
        record.status = ImportStatus.READY_TO_TRANSFORM
        self.db.add(record)
        self._snapshot_final_mappings(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_mappings_for_import(self, import_id: UUID) -> dict[str, str]:
        rows = self.db.execute(select(ImportMapping).where(ImportMapping.import_id == import_id)).scalars().all()
        return {row.source_column: row.target_field for row in rows}

    def save_transform_result(
        self,
        import_id: UUID,
        valid_row_count: int,
        invalid_row_count: int,
        cleaned_csv_key: str,
        normalized_json_key: str,
        validation_report_key: str,
        issues: list[dict[str, object]],
    ) -> ImportRecord:
        record = self.get_import(import_id)
        if record is None:
            raise LookupError("Import not found")

        result = (
            self.db.execute(select(ImportResult).where(ImportResult.import_id == record.id)).scalar_one_or_none()
        )
        if result is None:
            result = ImportResult(import_id=record.id)
        result.valid_row_count = valid_row_count
        result.invalid_row_count = invalid_row_count
        result.cleaned_csv_key = cleaned_csv_key
        result.normalized_json_key = normalized_json_key
        result.validation_report_key = validation_report_key
        self.db.add(result)

        self.db.query(ImportError).filter(ImportError.import_id == record.id).delete()
        for issue in issues:
            self.db.add(
                ImportError(
                    import_id=record.id,
                    row_number=issue.get("row_number"),
                    field_name=issue.get("field_name"),
                    severity=str(issue.get("severity", "error")),
                    message=str(issue.get("message", "")),
                )
            )

        record.status = ImportStatus.COMPLETED
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_result(self, import_id: UUID) -> tuple[ImportResult | None, list[ImportError]]:
        result = self.db.execute(select(ImportResult).where(ImportResult.import_id == import_id)).scalar_one_or_none()
        issues = self.db.execute(select(ImportError).where(ImportError.import_id == import_id)).scalars().all()
        return result, issues
