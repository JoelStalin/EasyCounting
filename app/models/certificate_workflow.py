"""Persistencia del workflow de obtencion y validacion de certificados."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base

JSONType = JSON().with_variant(SQLiteJSON(), "sqlite")


class PscRequest(Base):
    """Caso de tramite de certificado con una PSC."""

    __tablename__ = "psc_requests"
    __table_args__ = (
        UniqueConstraint("case_id", name="uq_psc_requests_case_id"),
        Index("ix_psc_requests_status", "status"),
        Index("ix_psc_requests_rnc", "rnc"),
    )

    case_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rnc: Mapped[str] = mapped_column(String(20), nullable=False)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    delegado_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    delegado_identificacion: Mapped[str] = mapped_column(String(50), nullable=False)
    psc_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    events: Mapped[list["WorkflowEvent"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="WorkflowEvent.id",
    )
    validations: Mapped[list["CertificateValidation"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="CertificateValidation.id",
    )
    reminders: Mapped[list["WorkflowReminder"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="WorkflowReminder.id",
    )
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="WorkflowExecution.id",
    )


class WorkflowEvent(Base):
    """Evento append-only del workflow de certificados."""

    __tablename__ = "workflow_events"
    __table_args__ = (
        Index("ix_workflow_events_case_id", "case_id"),
        Index("ix_workflow_events_event_type", "event_type"),
    )

    psc_request_id: Mapped[int] = mapped_column(ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    request: Mapped[PscRequest] = relationship(back_populates="events")


class CertificateValidation(Base):
    """Resultado de validacion tecnica de un .p12/.pfx para un case_id."""

    __tablename__ = "certificate_validations"
    __table_args__ = (
        Index("ix_certificate_validations_case_id", "case_id"),
        Index("ix_certificate_validations_valid", "valid"),
    )

    psc_request_id: Mapped[int] = mapped_column(ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    not_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    not_after: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    has_private_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    password_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped[PscRequest] = relationship(back_populates="validations")


class WorkflowReminder(Base):
    """Recordatorio y SLA para tareas humanas del workflow."""

    __tablename__ = "workflow_reminders"
    __table_args__ = (
        Index("ix_workflow_reminders_due_at", "due_at"),
        Index("ix_workflow_reminders_status", "status"),
    )

    psc_request_id: Mapped[int] = mapped_column(ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    request: Mapped[PscRequest] = relationship(back_populates="reminders")


class WorkflowExecution(Base):
    """Ejecucion auditada de un flujo autoasistido por case_id."""

    __tablename__ = "workflow_executions"
    __table_args__ = (
        UniqueConstraint("execution_id", name="uq_workflow_executions_execution_id"),
        Index("ix_workflow_executions_case_id", "case_id"),
        Index("ix_workflow_executions_status", "status"),
    )

    psc_request_id: Mapped[int] = mapped_column(ForeignKey("psc_requests.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(50), nullable=False)
    execution_id: Mapped[str] = mapped_column(String(80), nullable=False)
    current_step: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    last_success_step: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resume_token: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attempt: Mapped[int] = mapped_column(nullable=False, default=1)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    request: Mapped[PscRequest] = relationship(back_populates="executions")
    step_logs: Mapped[list["WorkflowStepLog"]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="WorkflowStepLog.id",
    )


class WorkflowStepLog(Base):
    """Bitacora por paso para reanudacion y diagnostico."""

    __tablename__ = "workflow_step_logs"
    __table_args__ = (
        Index("ix_workflow_step_logs_execution_id", "execution_id"),
        Index("ix_workflow_step_logs_step", "step"),
    )

    workflow_execution_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    execution_id: Mapped[str] = mapped_column(String(80), nullable=False)
    step: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    execution: Mapped[WorkflowExecution] = relationship(back_populates="step_logs")
