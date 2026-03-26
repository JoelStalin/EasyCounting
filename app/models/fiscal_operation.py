"""Durable fiscal operation and observability models."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, utcnow


JSONType = JSON().with_variant(SQLiteJSON(), "sqlite")


class FiscalOperation(Base):
    """Canonical durable workflow for DGII and Odoo operations."""

    __tablename__ = "fiscal_operations"
    __table_args__ = (
        UniqueConstraint("operation_id", name="uq_fiscal_operations_operation_id"),
        UniqueConstraint("operation_key", name="uq_fiscal_operations_operation_key"),
        Index("ix_fiscal_operations_tenant_state", "tenant_id", "state"),
        Index("ix_fiscal_operations_track_id", "dgii_track_id"),
        Index("ix_fiscal_operations_document", "document_type", "document_number"),
    )

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_key: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    environment: Mapped[str] = mapped_column(String(16), default="TEST")
    source_system: Mapped[str] = mapped_column(String(32), default="EASYCOUNTING")
    document_type: Mapped[str] = mapped_column(String(12))
    document_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(40), default="QUEUED", index=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="DOP")
    amount_total: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    dgii_track_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dgii_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    odoo_sync_state: Mapped[str] = mapped_column(String(32), default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    initiated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_transition_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    tenant = relationship("Tenant", backref="fiscal_operations")
    invoice = relationship("Invoice", back_populates="fiscal_operations", foreign_keys=[invoice_id])
    events: Mapped[List["FiscalOperationEvent"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="FiscalOperationEvent.id",
    )
    dgii_attempts: Mapped[List["DGIIAttempt"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="DGIIAttempt.id",
    )
    odoo_attempts: Mapped[List["OdooSyncAttempt"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="OdooSyncAttempt.id",
    )
    evidence_artifacts: Mapped[List["EvidenceArtifact"]] = relationship(
        back_populates="operation",
        cascade="all, delete-orphan",
        order_by="EvidenceArtifact.id",
    )


class FiscalOperationEvent(Base):
    """Append-only technical event for operation reconstruction."""

    __tablename__ = "fiscal_operation_events"
    __table_args__ = (
        Index("ix_fiscal_operation_events_operation_id", "operation_fk", "id"),
    )

    operation_fk: Mapped[int] = mapped_column(ForeignKey("fiscal_operations.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    operation: Mapped["FiscalOperation"] = relationship(back_populates="events")


class DGIIAttempt(Base):
    """Persisted DGII request/response attempt."""

    __tablename__ = "dgii_attempts"
    __table_args__ = (
        Index("ix_dgii_attempts_operation", "operation_fk", "attempt_no"),
        Index("ix_dgii_attempts_track_id", "track_id"),
    )

    operation_fk: Mapped[int] = mapped_column(ForeignKey("fiscal_operations.id", ondelete="CASCADE"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    endpoint: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_headers_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    immediate_response_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    track_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    operation: Mapped["FiscalOperation"] = relationship(back_populates="dgii_attempts")


class OdooSyncAttempt(Base):
    """Persisted Odoo synchronization attempt."""

    __tablename__ = "odoo_sync_attempts"
    __table_args__ = (
        Index("ix_odoo_sync_attempts_operation", "operation_fk", "attempt_no"),
        Index("ix_odoo_sync_attempts_remote", "remote_model", "remote_record_id"),
    )

    operation_fk: Mapped[int] = mapped_column(ForeignKey("fiscal_operations.id", ondelete="CASCADE"), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    remote_model: Mapped[str] = mapped_column(String(64), default="account.move")
    remote_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remote_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    operation: Mapped["FiscalOperation"] = relationship(back_populates="odoo_attempts")


class EvidenceArtifact(Base):
    """File-based evidence linked to an operation."""

    __tablename__ = "evidence_artifacts"
    __table_args__ = (
        Index("ix_evidence_artifacts_operation", "operation_fk", "artifact_type"),
    )

    operation_fk: Mapped[int] = mapped_column(ForeignKey("fiscal_operations.id", ondelete="CASCADE"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(40))
    file_path: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    operation: Mapped["FiscalOperation"] = relationship(back_populates="evidence_artifacts")


class ComprobanteCoverageResult(Base):
    """Coverage matrix row persisted for reproducible test evidence."""

    __tablename__ = "comprobante_coverage_results"
    __table_args__ = (
        UniqueConstraint("environment", "document_type", name="uq_comprobante_coverage_environment_type"),
    )

    environment: Mapped[str] = mapped_column(String(16), default="TEST")
    document_type: Mapped[str] = mapped_column(String(12), index=True)
    classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    odoo_supported: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    easycounting_supported: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    dgii_supported: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    sandbox_supported: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    supports_amount_0001: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    minimum_supported_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    last_operation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_status: Mapped[str] = mapped_column(String(32), default="PENDING")
    restriction_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
