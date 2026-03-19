"""Modelo de usuarios y RBAC."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.partner import PartnerAccount
from app.models.tenant import Tenant


class User(Base):
    """Usuarios autenticados con MFA y roles por tenant."""

    __tablename__ = "users"

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    partner_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("partner_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    mfa_secret: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="activo")

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    partner_account: Mapped[PartnerAccount | None] = relationship(back_populates="users")
