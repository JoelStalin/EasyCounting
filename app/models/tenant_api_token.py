from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User


class TenantApiToken(Base):
    __tablename__ = "tenant_api_tokens"
    __table_args__ = (
        Index("ix_tenant_api_tokens_tenant_id", "tenant_id"),
        Index("ix_tenant_api_tokens_token_hash", "token_hash", unique=True),
        Index("ix_tenant_api_tokens_revoked_at", "revoked_at"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, default="invoices:read")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tenant: Mapped[Tenant] = relationship(backref="api_tokens")
    created_by_user: Mapped[Optional[User]] = relationship()
