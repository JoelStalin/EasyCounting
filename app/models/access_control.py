"""Authorization, session and role-management models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TenantMembership(Base):
    """Role assignment for a user inside a tenant."""

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", "role", name="uq_tenant_memberships_user_tenant_role"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="memberships")
    tenant: Mapped["Tenant"] = relationship(back_populates="memberships")


class RoleChangeRequest(Base):
    """Approval workflow for elevated role changes."""

    __tablename__ = "role_change_requests"

    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    requested_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_role: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tenant: Mapped["Tenant | None"] = relationship(back_populates="role_change_requests")
    requested_by_user: Mapped["User"] = relationship(
        back_populates="role_change_requests_requested",
        foreign_keys=[requested_by_user_id],
    )
    reviewed_by_user: Mapped["User | None"] = relationship(
        back_populates="role_change_requests_reviewed",
        foreign_keys=[reviewed_by_user_id],
    )


class UserSession(Base):
    """Short-lived access session backed by a revocable refresh token."""

    __tablename__ = "user_sessions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    membership_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    active_tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    session_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    scope: Mapped[str] = mapped_column(String(255), default="")
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    membership: Mapped["TenantMembership | None"] = relationship(backref="sessions")
    active_tenant: Mapped["Tenant | None"] = relationship(backref="sessions")


class SensitiveActionToken(Base):
    """One-time tokens used for password/email and other sensitive operations."""

    __tablename__ = "sensitive_action_tokens"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(60), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    target_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sensitive_action_tokens")


class WebAuthnCredential(Base):
    """Persisted WebAuthn public-key credentials."""

    __tablename__ = "webauthn_credentials"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    credential_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(default=0)
    transports: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="webauthn_credentials")


class RecoveryCode(Base):
    """Backup recovery code for MFA recovery flows."""

    __tablename__ = "recovery_codes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="recovery_codes")


class PartnerCommissionRule(Base):
    """Commercial rule applied to a partner account."""

    __tablename__ = "partner_commission_rules"

    partner_account_id: Mapped[int] = mapped_column(
        ForeignKey("partner_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    percentage_rate: Mapped[float] = mapped_column(Numeric(8, 4), default=0)
    cap_amount: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    partner_account: Mapped["PartnerAccount"] = relationship(backref="commission_rules")


class PartnerCommissionLedger(Base):
    """Commission accrual per invoice for a partner."""

    __tablename__ = "partner_commission_ledger"

    partner_account_id: Mapped[int] = mapped_column(
        ForeignKey("partner_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("partner_commission_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    rate_applied: Mapped[float] = mapped_column(Numeric(8, 4), default=0)
    commission_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    partner_account: Mapped["PartnerAccount"] = relationship(backref="commission_entries")
    tenant: Mapped["Tenant"] = relationship(backref="commission_entries")
    invoice: Mapped["Invoice | None"] = relationship(backref="commission_entries")
    rule: Mapped["PartnerCommissionRule | None"] = relationship(backref="ledger_entries")

