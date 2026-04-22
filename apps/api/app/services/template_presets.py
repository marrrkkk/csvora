"""Optional starter payloads for templates.

These dicts mirror the JSON shape of ``TemplateCreateRequest.version`` and are **not**
enforced by the API. Use them as copy-paste seed data when defining a contacts-style
schema; authority always comes from the template version you persist.
"""

from __future__ import annotations

from typing import Any


def contacts_version_starter() -> dict[str, Any]:
    """Example version block: common contact fields plus template-level ``require_one_of``."""
    return {
        "strict_mode": False,
        "auto_accept_confidence": 0.85,
        "review_threshold": 0.6,
        "ai_enabled": False,
        "validation_rules": {"require_one_of": [["email", "phone"]]},
        "fields": [
            {
                "field_key": "first_name",
                "label": "First name",
                "value_type": "string",
                "is_builtin": True,
                "is_required": False,
                "aliases": ["firstname", "given name"],
                "allow_empty": True,
                "sort_order": 0,
            },
            {
                "field_key": "last_name",
                "label": "Last name",
                "value_type": "string",
                "is_builtin": True,
                "is_required": False,
                "aliases": ["lastname", "surname"],
                "allow_empty": True,
                "sort_order": 1,
            },
            {
                "field_key": "email",
                "label": "Email",
                "value_type": "email",
                "is_builtin": True,
                "is_required": False,
                "aliases": ["e-mail", "mail"],
                "allow_empty": True,
                "sort_order": 2,
            },
            {
                "field_key": "phone",
                "label": "Phone",
                "value_type": "phone",
                "is_builtin": True,
                "is_required": False,
                "aliases": ["mobile", "tel"],
                "allow_empty": True,
                "sort_order": 3,
            },
        ],
    }
