"""Recurring invoice schedules and execution history."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User


class RecurringInvoiceSchedule(Base):
    __tablename__ = "recurring_invoice_schedules"
    __table_args__ = (
        Index("ix_recurring_invoice_schedules_tenant_status", "tenant_id", "status"),
        Index("ix_recurring_invoice_schedules_next_run_at", "next_run_at"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_generated_invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tipo_ecf: Mapped[str] = mapped_column(String(3), nullable=False)
    rnc_receptor: Mapped[str | None] = mapped_column(String(11), nullable=True)
    total: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    tenant: Mapped[Tenant] = relationship(backref="recurring_invoice_schedules")
    created_by_user: Mapped[Optional[User]] = relationship()
    last_generated_invoice = relationship("Invoice", foreign_keys=[last_generated_invoice_id])
    executions: Mapped[list["RecurringInvoiceExecution"]] = relationship(
        back_populates="schedule",
        cascade="all, delete-orphan",
    )


class RecurringInvoiceExecution(Base):
    __tablename__ = "recurring_invoice_executions"
    __table_args__ = (
        UniqueConstraint("schedule_id", "scheduled_for", name="ux_recurring_invoice_schedule_occurrence"),
        Index("ix_recurring_invoice_executions_tenant_id", "tenant_id"),
        Index("ix_recurring_invoice_executions_scheduled_for", "scheduled_for"),
    )

    schedule_id: Mapped[int] = mapped_column(ForeignKey("recurring_invoice_schedules.id", ondelete="CASCADE"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="generated")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    schedule: Mapped[RecurringInvoiceSchedule] = relationship(back_populates="executions")
    tenant: Mapped[Tenant] = relationship()
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
