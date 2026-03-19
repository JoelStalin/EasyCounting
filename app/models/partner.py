"""Modelos para el portal de revendedores y su relacion con tenants."""
from __future__ import annotations

from typing import List

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PartnerAccount(Base):
    """Agrupa usuarios reseller/operator/auditor bajo una misma cuenta comercial."""

    __tablename__ = "partner_accounts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="activo")

    users: Mapped[List["User"]] = relationship(back_populates="partner_account")
    tenant_assignments: Mapped[List["PartnerTenantAssignment"]] = relationship(
        back_populates="partner_account",
        cascade="all, delete-orphan",
    )


class PartnerTenantAssignment(Base):
    """Define los tenants visibles y operables para una cuenta reseller."""

    __tablename__ = "partner_tenant_assignments"
    __table_args__ = (
        UniqueConstraint("partner_account_id", "tenant_id", name="ux_partner_tenant_assignment"),
    )

    partner_account_id: Mapped[int] = mapped_column(ForeignKey("partner_accounts.id", ondelete="CASCADE"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    can_emit: Mapped[bool] = mapped_column(Boolean, default=True)
    can_manage: Mapped[bool] = mapped_column(Boolean, default=True)

    partner_account: Mapped[PartnerAccount] = relationship(back_populates="tenant_assignments")
    tenant: Mapped["Tenant"] = relationship(backref="partner_assignments")
