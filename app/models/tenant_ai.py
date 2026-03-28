"""Tenant-specific AI provider configuration."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TenantAIProvider(Base):
    """Configuración de proveedores IA por tenant."""

    __tablename__ = "tenant_ai_providers"

    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(120), index=True)
    provider_type: Mapped[str] = mapped_column(String(40), index=True)  # openai, gemini, anthropic, local
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    base_url: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str] = mapped_column(String(160))
    encrypted_api_key: Mapped[str | None] = mapped_column(Text)
    
    # Extra fields
    organization_id: Mapped[str | None] = mapped_column(String(120))
    project_id: Mapped[str | None] = mapped_column(String(120))
    api_version: Mapped[str | None] = mapped_column(String(64))
    
    system_prompt: Mapped[str | None] = mapped_column(Text)
    extra_headers_json: Mapped[str | None] = mapped_column(Text)
    timeout_seconds: Mapped[float] = mapped_column(Float, default=30.0)
    max_completion_tokens: Mapped[int] = mapped_column(default=1000)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="ai_providers")
