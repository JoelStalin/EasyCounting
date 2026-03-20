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
    expiration_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    issuer_tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    issuer_fiscal_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("fiscal_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    receiver_fiscal_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("fiscal_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    issuer_tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    issuer_legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issuer_trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issuer_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issuer_municipality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    issuer_province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rnc_receptor: Mapped[str | None] = mapped_column(String(11), index=True, nullable=True)
    receptor_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receptor_direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receptor_municipio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    receptor_provincia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    xml_path: Mapped[str] = mapped_column(String(255))
    xml_hash: Mapped[str] = mapped_column(String(128))
    ri_html_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ri_pdf_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ri_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    qr_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    estado_dgii: Mapped[str] = mapped_column(String(30), default="pendiente")
    track_id: Mapped[str | None] = mapped_column(String(64))
    codigo_seguridad: Mapped[str | None] = mapped_column(String(6))
    total: Mapped[float] = mapped_column(Numeric(16, 2))
    fecha_emision: Mapped[datetime] = mapped_column(default=utcnow)
    contabilizado: Mapped[bool] = mapped_column(Boolean, default=False)
    accounted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    asiento_referencia: Mapped[str | None] = mapped_column(String(64))

    tenant: Mapped[Tenant] = relationship(backref="invoices")
    issuer_tenant: Mapped[Tenant | None] = relationship(foreign_keys=[issuer_tenant_id], backref="issued_invoices")
    ledger_entries: Mapped[List["InvoiceLedgerEntry"]] = relationship("InvoiceLedgerEntry", back_populates="invoice")
    line_items: Mapped[List["InvoiceLine"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class InvoiceLine(Base):
    """Detailed persisted invoice line used by the RI and integrations."""

    __tablename__ = "invoice_lines"
    __table_args__ = (Index("ix_invoice_lines_invoice_id", "invoice_id"),)

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    line_number: Mapped[int] = mapped_column(default=1)
    cantidad: Mapped[float] = mapped_column(Numeric(16, 2), default=1)
    billing_indicator: Mapped[str | None] = mapped_column(String(20), nullable=True)
    descripcion: Mapped[str] = mapped_column(String(255))
    unidad_medida: Mapped[str | None] = mapped_column(String(40), nullable=True)
    precio_unitario: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    itbis_rate: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    itbis_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    other_tax_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    line_total: Mapped[float] = mapped_column(Numeric(16, 2), default=0)

    invoice: Mapped[Invoice] = relationship(back_populates="line_items")
    tenant: Mapped[Tenant] = relationship(backref="invoice_lines")
