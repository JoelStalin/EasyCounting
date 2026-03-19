from __future__ import annotations

import re
from typing import Any


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<key>\b(?:password|passwd|contrase(?:n|ñ)a|secret|token|cookie|session|api[_ -]?key|"
    r"aws_access_key_id|aws_secret_access_key|aws_session_token|smtp_pass|client_secret)\b"
    r"\s*(?:[:=]\s*|\s+))(?P<value>[^\s`\"']+)",
    re.IGNORECASE,
)
BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._=-]+\b", re.IGNORECASE)
COOKIE_PATTERN = re.compile(r"\b(?:set-cookie|cookie)\s*:\s*[^;\n]+", re.IGNORECASE)
QUERY_SECRET_PATTERN = re.compile(r"([?&](?:token|code|session|secret|apikey|api_key)=)[^&\s]+", re.IGNORECASE)
RNC_PATTERN = re.compile(r"\b(?:rnc|cedula|cédula|fiscal(?:[_ -]?id)?)\s*[:=]?\s*\d{9,13}\b", re.IGNORECASE)
PEM_BLOCK_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]+-----.*?-----END [A-Z ]+-----",
    re.DOTALL,
)


def redact_text(value: str, *, extra_secrets: list[str] | None = None) -> tuple[str, bool]:
    text = value
    changed = False

    replacements = [
        (EMAIL_PATTERN, "<EMAIL_REDACTED>"),
        (BEARER_PATTERN, "Bearer <SECRET_REDACTED>"),
        (COOKIE_PATTERN, "cookie: <SECRET_REDACTED>"),
        (QUERY_SECRET_PATTERN, r"\1<SECRET_REDACTED>"),
        (RNC_PATTERN, "<FISCAL_ID_REDACTED>"),
        (PEM_BLOCK_PATTERN, "<PEM_BLOCK_REDACTED>"),
    ]
    for pattern, replacement in replacements:
        updated = pattern.sub(replacement, text)
        if updated != text:
            changed = True
            text = updated

    def _replace_assignment(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return f"{match.group('key')}<SECRET_REDACTED>"

    text = SENSITIVE_ASSIGNMENT_PATTERN.sub(_replace_assignment, text)

    for secret in extra_secrets or []:
        if not secret:
            continue
        escaped = re.escape(secret)
        updated = re.sub(escaped, "<SECRET_REDACTED>", text, flags=re.IGNORECASE)
        if updated != text:
            changed = True
            text = updated

    return text, changed


def redact_value(value: Any, *, extra_secrets: list[str] | None = None) -> tuple[Any, bool]:
    if isinstance(value, str):
        return redact_text(value, extra_secrets=extra_secrets)
    if isinstance(value, list):
        changed = False
        items: list[Any] = []
        for item in value:
            sanitized, item_changed = redact_value(item, extra_secrets=extra_secrets)
            changed = changed or item_changed
            items.append(sanitized)
        return items, changed
    if isinstance(value, dict):
        changed = False
        result: dict[str, Any] = {}
        for key, item in value.items():
            sanitized, item_changed = redact_value(item, extra_secrets=extra_secrets)
            changed = changed or item_changed
            result[str(key)] = sanitized
        return result, changed
    return value, False
