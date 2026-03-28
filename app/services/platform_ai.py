"""Helpers for encrypted platform AI provider configuration."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.settings import settings
from app.models.platform_ai import PlatformAIProvider

SUPPORTED_AI_PROVIDER_TYPES = {
    "openai": "ChatGPT / OpenAI",
    "gemini": "Google Gemini",
    "anthropic": "Claude / Anthropic",
    "openai_compatible": "OpenAI Compatible",
}

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "anthropic": "https://api.anthropic.com/v1",
}


@dataclass(slots=True)
class PlatformAIProviderRuntime:
    provider_id: int
    display_name: str
    provider_type: str
    base_url: str | None
    model: str
    api_key: str | None
    organization_id: str | None
    project_id: str | None
    api_version: str | None
    system_prompt: str | None
    extra_headers: dict[str, str]
    timeout_seconds: float
    max_completion_tokens: int


def ensure_platform_ai_table(db: Session) -> None:
    PlatformAIProvider.__table__.create(bind=db.get_bind(), checkfirst=True)


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def mask_secret(raw_value: str | None) -> str | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * max(len(value) - 8, 4)}{value[-4:]}"


def parse_extra_headers(raw_json: str | None) -> dict[str, str]:
    if not raw_json:
        return {}
    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    parsed: dict[str, str] = {}
    for key, value in decoded.items():
        key_text = str(key).strip()
        value_text = str(value).strip()
        if key_text and value_text:
            parsed[key_text] = value_text
    return parsed


def dumps_extra_headers(headers: dict[str, str] | None) -> str | None:
    if not headers:
        return None
    return json.dumps(headers, ensure_ascii=True, sort_keys=True)


def normalize_base_url(provider_type: str, base_url: str | None) -> str | None:
    value = (base_url or "").strip()
    if value:
        return value
    return DEFAULT_BASE_URLS.get(provider_type)


def load_default_runtime_provider(db: Session) -> PlatformAIProviderRuntime | None:
    try:
        ensure_platform_ai_table(db)
        provider = db.scalar(
            select(PlatformAIProvider)
            .where(PlatformAIProvider.enabled.is_(True))
            .order_by(PlatformAIProvider.is_default.desc(), PlatformAIProvider.updated_at.desc(), PlatformAIProvider.id.desc())
            .limit(1)
        )
    except Exception:  # noqa: BLE001
        return None
    if not provider:
        return None

    extra_headers = parse_extra_headers(provider.extra_headers_json)
    if provider.provider_type == "openai":
        if provider.organization_id:
            extra_headers.setdefault("OpenAI-Organization", provider.organization_id)
        if provider.project_id:
            extra_headers.setdefault("OpenAI-Project", provider.project_id)

    return PlatformAIProviderRuntime(
        provider_id=provider.id,
        display_name=provider.display_name,
        provider_type=provider.provider_type,
        base_url=normalize_base_url(provider.provider_type, provider.base_url),
        model=provider.model,
        api_key=decrypt_secret(provider.encrypted_api_key),
        organization_id=provider.organization_id,
        project_id=provider.project_id,
        api_version=provider.api_version,
        system_prompt=provider.system_prompt,
        extra_headers=extra_headers,
        timeout_seconds=float(provider.timeout_seconds),
        max_completion_tokens=int(provider.max_completion_tokens),
    )
