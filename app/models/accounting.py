"""Modelos para contabilidad y configuración de tenants."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
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

    tenant: Mapped[Tenant] = relationship(backref="settings", single_parent=True, uselist=False)


class InvoiceLedgerEntry(Base):
    """Asiento contable simple asociado a un comprobante."""

    __tablename__ = "invoice_ledger_entries"

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    referencia: Mapped[str] = mapped_column(String(64))
    cuenta: Mapped[str] = mapped_column(String(64))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    debit: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    tenant: Mapped[Tenant] = relationship(backref="ledger_entries")
    invoice: Mapped["Invoice | None"] = relationship(back_populates="ledger_entries")
