import re

COUNTRY_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
}


def normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    compact = re.sub(r"\s+", " ", value).strip()
    return compact or None


def normalize_email(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value is None:
        return None
    return value.lower()


def normalize_phone(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value is None:
        return None
    cleaned = re.sub(r"[^\d+]", "", value)
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    return cleaned or None


def normalize_country(value: str | None) -> str | None:
    value = normalize_whitespace(value)
    if value is None:
        return None
    lowered = value.lower()
    if lowered in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lowered]
    return value


def normalize_tags(value: str | None) -> list[str]:
    value = normalize_whitespace(value)
    if value is None:
        return []
    tokens = re.split(r"[;,|]", value)
    seen: set[str] = set()
    output: list[str] = []
    for token in tokens:
        tag = normalize_whitespace(token)
        if not tag:
            continue
        lowered = tag.lower()
        if lowered not in seen:
            seen.add(lowered)
            output.append(tag)
    return output
