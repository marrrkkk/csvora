from enum import StrEnum


class ImportStatus(StrEnum):
    CREATED = "created"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    NEEDS_REVIEW = "needs_review"
    READY_TO_TRANSFORM = "ready_to_transform"
    TRANSFORMING = "transforming"
    COMPLETED = "completed"
    FAILED = "failed"


class TemplateStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemplateFieldValueType(StrEnum):
    STRING = "string"
    EMAIL = "email"
    PHONE = "phone"
    INT = "int"
    FLOAT = "float"
    DATE = "date"
    ENUM = "enum"
    BOOL = "bool"
