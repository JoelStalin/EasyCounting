"""Modelo de comprobantes electrónicos."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.tenant import Tenant


class Invoice(Base):
    """Representa un e-CF emitido por la plataforma."""

    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "encf", name="ux_invoices_tenant_encf"),
        Index("ix_invoices_estado", "estado_dgii"),
        Index("ix_invoices_track_id", "track_id"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    encf: Mapped[str] = mapped_column(String(20), index=True)
    tipo_ecf: Mapped[str] = mapped_column(String(3))
    rnc_receptor: Mapped[str | None] = mapped_column(String(11), index=True, nullable=True)
    xml_path: Mapped[str] = mapped_column(String(255))
    xml_hash: Mapped[str] = mapped_column(String(128))
    estado_dgii: Mapped[str] = mapped_column(String(30), default="pendiente")
    track_id: Mapped[str | None] = mapped_column(String(64))
    codigo_seguridad: Mapped[str | None] = mapped_column(String(6))
    total: Mapped[float] = mapped_column(Numeric(16, 2))
    fecha_emision: Mapped[datetime] = mapped_column(default=utcnow)
    contabilizado: Mapped[bool] = mapped_column(Boolean, default=False)
    accounted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    asiento_referencia: Mapped[str | None] = mapped_column(String(64))

    tenant: Mapped[Tenant] = relationship(backref="invoices")
    ledger_entries: Mapped[List["InvoiceLedgerEntry"]] = relationship("InvoiceLedgerEntry", back_populates="invoice")
