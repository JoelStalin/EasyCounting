"""Modelos para contabilidad y configuración de tenants."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.tenant import Tenant

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class TenantSettings(Base):
    """Parámetros contables y operativos por empresa."""

    __tablename__ = "tenant_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant"),)

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    moneda: Mapped[str] = mapped_column(String(5), default="DOP")
    cuenta_ingresos: Mapped[Optional[str]] = mapped_column(String(64))
    cuenta_itbis: Mapped[Optional[str]] = mapped_column(String(64))
    cuenta_retenciones: Mapped[Optional[str]] = mapped_column(String(64))
    dias_credito: Mapped[int] = mapped_column(default=0)
    correo_facturacion: Mapped[Optional[str]] = mapped_column(String(255))
    telefono_contacto: Mapped[Optional[str]] = mapped_column(String(25))
    notas: Mapped[Optional[str]] = mapped_column(String(512))
    rounding_policy: Mapped[str] = mapped_column(String(32), default="HALF_UP")
    odoo_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    odoo_api_url: Mapped[Optional[str]] = mapped_column(String(255))
    odoo_database: Mapped[Optional[str]] = mapped_column(String(120))
    odoo_company_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_sales_journal_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_purchase_journal_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_fiscal_position_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_payment_term_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_currency_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_customer_document_type_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_vendor_document_type_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_credit_note_document_type_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_debit_note_document_type_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_sales_tax_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_purchase_tax_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_zero_tax_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    odoo_partner_vat_prefix: Mapped[Optional[str]] = mapped_column(String(12))
    odoo_journal_code_hint: Mapped[Optional[str]] = mapped_column(String(32))
    odoo_api_key_ref: Mapped[Optional[str]] = mapped_column(String(128))

    tenant: Mapped[Tenant] = relationship(backref="settings", single_parent=True, uselist=False)


class InvoiceLedgerEntry(Base):
    """Asiento contable simple asociado a un comprobante."""

    __tablename__ = "invoice_ledger_entries"

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    referencia: Mapped[str] = mapped_column(String(64))
    cuenta: Mapped[str] = mapped_column(String(64))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    debit: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    credit: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    tenant: Mapped[Tenant] = relationship(backref="ledger_entries")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="ledger_entries")
