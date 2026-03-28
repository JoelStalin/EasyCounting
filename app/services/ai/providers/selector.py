"""AI Provider selector and factory."""
from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.platform_ai import PlatformAIProvider
from app.models.tenant_ai import TenantAIProvider
from app.models.user_ai import UserAIProvider
from app.services.platform_ai import decrypt_secret, parse_extra_headers
from app.services.ai.providers.base import BaseLLMProvider
from app.services.ai.providers.openai import OpenAIProvider
from app.services.ai.providers.anthropic import AnthropicProvider
from app.services.ai.providers.gemini import GeminiProvider
from app.infra.settings import settings


class ProviderSelector:
    """Selecciona y construye el proveedor de IA basado en la jerarquia de configuracion."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_provider(self, tenant_id: int, user_id: int | None = None) -> BaseLLMProvider:
        # 1. Intentar proveedor por defecto del usuario
        if user_id is not None:
            user_provider = self.db.scalar(
                select(UserAIProvider)
                .where(UserAIProvider.user_id == user_id, UserAIProvider.enabled.is_(True))
                .order_by(UserAIProvider.is_default.desc(), UserAIProvider.id.desc())
                .limit(1)
            )
            if user_provider:
                return self._build_from_model(user_provider)

        # 2. Intentar proveedor por defecto del tenant
        tenant_provider = self.db.scalar(
            select(TenantAIProvider)
            .where(TenantAIProvider.tenant_id == tenant_id, TenantAIProvider.enabled.is_(True))
            .order_by(TenantAIProvider.is_default.desc(), TenantAIProvider.id.desc())
            .limit(1)
        )
        if tenant_provider:
            return self._build_from_model(tenant_provider)

        # 3. Intentar proveedor por defecto de la plataforma
        platform_provider = self.db.scalar(
            select(PlatformAIProvider)
            .where(PlatformAIProvider.enabled.is_(True))
            .order_by(PlatformAIProvider.is_default.desc(), PlatformAIProvider.id.desc())
            .limit(1)
        )
        if platform_provider:
            return self._build_from_model(platform_provider)

        # 4. Fallback al default local de settings
        return self._build_local_default()

    def _build_from_model(self, model: PlatformAIProvider | TenantAIProvider | UserAIProvider) -> BaseLLMProvider:
        config = {
            "base_url": model.base_url,
            "api_key": decrypt_secret(model.encrypted_api_key),
            "model": model.model,
            "timeout": float(model.timeout_seconds),
            "max_tokens": int(model.max_completion_tokens),
            "extra_headers": parse_extra_headers(model.extra_headers_json),
        }

        if model.provider_type == "openai" or model.provider_type == "openai_compatible":
            return OpenAIProvider(**config)
        if model.provider_type == "anthropic":
            return AnthropicProvider(**config)
        if model.provider_type == "gemini":
            return GeminiProvider(**config)
        
        # Default to OpenAI compatible if unknown
        return OpenAIProvider(**config)

    def _build_local_default(self) -> BaseLLMProvider:
        """Construye el proveedor local configurado en settings (Open Source self-hosted)."""
        return OpenAIProvider(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            max_tokens=settings.llm_max_completion_tokens,
        )
