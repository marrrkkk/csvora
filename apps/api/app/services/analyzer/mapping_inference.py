"""Legacy column-to-field inference for imports without a template.

Uses a fixed contact-oriented vocabulary (CANONICAL_FIELDS / ALIASES). Template-bound
imports use template field metadata instead; see ``infer_template_mappings``.
"""

from difflib import SequenceMatcher

CANONICAL_FIELDS = [
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone",
    "company",
    "job_title",
    "city",
    "state",
    "country",
    "tags",
    "notes",
]

ALIASES = {
    "email": {"email", "e-mail", "mail", "email address"},
    "phone": {"phone", "mobile", "mobile no", "mobile number", "telephone"},
    "company": {"company", "company name", "organization"},
    "first_name": {"first name", "firstname", "given name"},
    "last_name": {"last name", "lastname", "surname"},
    "full_name": {"full name", "name"},
    "job_title": {"title", "job title", "role"},
    "city": {"city", "town"},
    "state": {"state", "province", "region"},
    "country": {"country", "nation"},
    "tags": {"tags", "labels", "segments"},
    "notes": {"notes", "comments", "description"},
}


def infer_mapping(columns: list[str]) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []
    for column in columns:
        normalized = column.strip().lower()
        best_field = None
        best_score = 0.0
        reason = "fuzzy"

        for target, alias_set in ALIASES.items():
            if normalized in alias_set:
                best_field = target
                best_score = 0.98
                reason = "alias_exact"
                break

        if best_field is None:
            for target in CANONICAL_FIELDS:
                score = SequenceMatcher(None, normalized.replace("_", " "), target.replace("_", " ")).ratio()
                if score > best_score:
                    best_score = score
                    best_field = target

        if best_field and best_score >= 0.55:
            suggestions.append(
                {
                    "source_column": column,
                    "target_field": best_field,
                    "confidence": round(float(best_score), 3),
                    "reason": reason,
                }
            )
    return suggestions
