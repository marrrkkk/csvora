from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.services.ai.schemas import AIMappingAssistResponse

logger = logging.getLogger(__name__)


def call_mapping_assist(
    settings: Settings,
    *,
    system_prompt: str,
    user_payload: dict[str, Any],
) -> AIMappingAssistResponse | None:
    if not settings.openrouter_api_key or not settings.ai_mapping_enabled:
        return None

    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    body = {
        "model": settings.openrouter_model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Return JSON only matching schema {\"rows\": [...]} with keys source_column, target_field, confidence, rationale.\n"
                + json.dumps(user_payload, ensure_ascii=False),
            },
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_http_referer,
        "X-Title": settings.openrouter_app_title,
    }
    last_err: str | None = None
    for attempt in range(max(1, settings.ai_max_retries)):
        try:
            timeout = httpx.Timeout(settings.ai_timeout_seconds)
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return AIMappingAssistResponse.model_validate(parsed)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValidationError, IndexError) as exc:
            last_err = str(exc)
            logger.warning("openrouter_mapping_assist_failed", extra={"attempt": attempt, "error": last_err})
    logger.error("openrouter_mapping_assist_gave_up", extra={"error": last_err})
    return None
