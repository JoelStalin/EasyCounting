"""Modelo de usuarios y RBAC."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
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
    global_role: Mapped[str] = mapped_column(String(20), default="USER")
    status: Mapped[str] = mapped_column(String(20), default="activo")
    last_password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    partner_account: Mapped[PartnerAccount | None] = relationship(back_populates="users")
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )
    fiscal_profile: Mapped["FiscalProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )
    memberships: Mapped[list["TenantMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sensitive_action_tokens: Mapped[list["SensitiveActionToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    webauthn_credentials: Mapped[list["WebAuthnCredential"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recovery_codes: Mapped[list["RecoveryCode"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    role_change_requests_requested: Mapped[list["RoleChangeRequest"]] = relationship(
        back_populates="requested_by_user",
        foreign_keys="RoleChangeRequest.requested_by_user_id",
    )
    role_change_requests_reviewed: Mapped[list["RoleChangeRequest"]] = relationship(
        back_populates="reviewed_by_user",
        foreign_keys="RoleChangeRequest.reviewed_by_user_id",
    )
    external_identities: Mapped[list["UserExternalIdentity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_challenges: Mapped[list["AuthLoginChallenge"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_tickets: Mapped[list["AuthLoginTicket"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    view_tours: Mapped[list["UserViewTour"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
