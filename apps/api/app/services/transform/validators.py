import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{7,15}$")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


def is_valid_phone(value: str) -> bool:
    return bool(PHONE_RE.match(value))


def is_empty_contact_row(row: dict[str, object]) -> bool:
    for value in row.values():
        if isinstance(value, list) and value:
            return False
        if isinstance(value, str) and value.strip():
            return False
    return True
