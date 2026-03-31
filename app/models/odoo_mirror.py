"""Tablas espejo para sincronizacion Odoo -> EasyCounting por tenant."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.types import PortableJSONB

from app.models.base import Base
from app.models.tenant import Tenant


class OdooPartnerMirror(Base):
    __tablename__ = "odoo_partner_mirror"
    __table_args__ = (
        UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_partner_mirror_tenant_odoo"),
        Index("ix_odoo_partner_mirror_tenant_kind", "tenant_id", "partner_kind"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    odoo_id: Mapped[int] = mapped_column(index=True)
    partner_kind: Mapped[str] = mapped_column(String(16), default="customer")
    name: Mapped[str] = mapped_column(String(255))
    vat: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    company_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    raw_json: Mapped[dict] = mapped_column(PortableJSONB, default=dict)
    synced_at: Mapped[datetime] = mapped_column(DateTime)

    tenant: Mapped[Tenant] = relationship(backref="odoo_partners")


class OdooProductMirror(Base):
    __tablename__ = "odoo_product_mirror"
    __table_args__ = (
        UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_product_mirror_tenant_odoo"),
        Index("ix_odoo_product_mirror_tenant_default_code", "tenant_id", "default_code"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    odoo_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255))
    default_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    list_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    standard_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    active: Mapped[bool] = mapped_column(default=True)
    raw_json: Mapped[dict] = mapped_column(PortableJSONB, default=dict)
    synced_at: Mapped[datetime] = mapped_column(DateTime)

    tenant: Mapped[Tenant] = relationship(backref="odoo_products")


class OdooInvoiceMirror(Base):
    __tablename__ = "odoo_invoice_mirror"
    __table_args__ = (
        UniqueConstraint("tenant_id", "odoo_id", name="ux_odoo_invoice_mirror_tenant_odoo"),
        Index("ix_odoo_invoice_mirror_tenant_state", "tenant_id", "state"),
        Index("ix_odoo_invoice_mirror_tenant_move_name", "tenant_id", "move_name"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    odoo_id: Mapped[int] = mapped_column(index=True)
    move_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    move_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payment_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    invoice_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    partner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    partner_vat: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    amount_total: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    amount_tax: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    amount_untaxed: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    encf: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    raw_json: Mapped[dict] = mapped_column(PortableJSONB, default=dict)
    lines_json: Mapped[dict] = mapped_column(PortableJSONB, default=dict)
    synced_at: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant: Mapped[Tenant] = relationship(backref="odoo_invoices")
