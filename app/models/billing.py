"""Modelos de planes de facturación y registros de uso."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Plan(Base):
    """Plan de subscripción asociado a un tenant."""

    __tablename__ = "billing_plans"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    precio_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    precio_por_documento: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0"))
    documentos_incluidos: Mapped[int] = mapped_column(default=0)
    max_facturas_mes: Mapped[int] = mapped_column(default=0)
    max_facturas_por_receptor_mes: Mapped[int] = mapped_column(default=0)
    max_monto_por_factura: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=Decimal("0"))
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))

    tenants: Mapped[List["Tenant"]] = relationship("Tenant", back_populates="plan", foreign_keys="Tenant.plan_id")
    usage_records: Mapped[List["UsageRecord"]] = relationship("UsageRecord", back_populates="plan")


class UsageRecord(Base):
    """Registro de cargos por utilización de e-CF."""

    __tablename__ = "billing_usage_records"
    __table_args__ = (
        Index("ix_usage_records_tenant_fecha", "tenant_id", "fecha"),
        Index("ix_usage_records_track_id", "track_id"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("billing_plans.id", ondelete="SET NULL"))
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    ecf_type: Mapped[str] = mapped_column(String(6))
    track_id: Mapped[Optional[str]] = mapped_column(String(64))
    monto_cargado: Mapped[Decimal] = mapped_column(Numeric(16, 4), default=Decimal("0"))
    fecha: Mapped[datetime] = mapped_column(default=utcnow)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="usage_records")
    plan: Mapped[Optional[Plan]] = relationship("Plan", back_populates="usage_records")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")
