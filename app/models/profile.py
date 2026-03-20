"""Extended personal and fiscal profile models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserProfile(Base):
    """Normalized personal/contact information for a user."""

    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    avatar_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    alternate_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_primary: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address_line_1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    municipality: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    economic_activity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(20), default="es-DO")
    timezone: Mapped[str] = mapped_column(String(64), default="America/Santo_Domingo")
    notification_settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    security_settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    regional_settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    privacy_settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="profile")


class FiscalProfile(Base):
    """Fiscal data reused for issuers, receivers and readiness validation."""

    __tablename__ = "fiscal_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_fiscal_profiles_user"),
        UniqueConstraint("tenant_id", name="uq_fiscal_profiles_tenant"),
    )

    owner_type: Mapped[str] = mapped_column(String(20), default="TENANT")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    persona_tipo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tax_id_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fiscal_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    municipality: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    representative_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    commercial_activity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dgii_certificate_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dgii_certificate_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_billing_ready_override: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User | None"] = relationship(back_populates="fiscal_profile")
    tenant: Mapped["Tenant | None"] = relationship(back_populates="fiscal_profile")

