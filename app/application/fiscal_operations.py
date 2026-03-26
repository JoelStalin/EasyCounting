"""Durable fiscal operation orchestration helpers."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fiscal_operation import (
    ComprobanteCoverageResult,
    DGIIAttempt,
    EvidenceArtifact,
    FiscalOperation,
    FiscalOperationEvent,
    OdooSyncAttempt,
)
from app.shared.time import utcnow

FINAL_OPERATION_STATES = {"ACCEPTED", "ACCEPTED_CONDITIONAL", "REJECTED", "FAILED_TECHNICAL", "CANCELLED"}
ACCEPTED_REMOTE_STATES = {"ACEPTADO", "ACEPTADA", "ACCEPTED"}
ACCEPTED_CONDITIONAL_REMOTE_STATES = {"ACEPTADO_CONDICIONAL", "ACEPTADA_CONDICIONAL", "ACCEPTED_CONDITIONAL"}
REJECTED_REMOTE_STATES = {"RECHAZADO", "REJECTADA", "REJECTED", "DEVUELTO"}


def canonical_dgii_environment(value: str | None) -> str:
    normalized = (value or "TEST").strip().upper()
    if normalized in {"PRECERT", "TEST", "TESTECF"}:
        return "TEST"
    if normalized in {"LOCAL"}:
        return "LOCAL"
    if normalized == "CERT":
        return "CERT"
    if normalized == "PROD":
        return "PROD"
    return normalized or "TEST"


def build_operation_key(*, tenant_id: int, document_type: str, document_number: str | None, environment: str, payload_hash: str | None, source_system: str) -> str:
    raw = "|".join(
        [
            str(tenant_id),
            document_type,
            document_number or "",
            environment,
            payload_hash or "",
            source_system,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def map_remote_status(remote_status: str | None) -> str:
    value = (remote_status or "").strip().upper()
    if value in ACCEPTED_REMOTE_STATES:
        return "ACCEPTED"
    if value in ACCEPTED_CONDITIONAL_REMOTE_STATES:
        return "ACCEPTED_CONDITIONAL"
    if value in REJECTED_REMOTE_STATES:
        return "REJECTED"
    return "QUERYING_TRACK_STATUS"


class FiscalOperationService:
    """Durable operations service backed by SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start_operation(
        self,
        *,
        tenant_id: int,
        document_type: str,
        document_number: str | None,
        environment: str,
        source_system: str,
        payload_hash: str | None,
        amount_total: Decimal,
        currency: str,
        request_id: str | None = None,
        initiated_by: str | None = None,
        metadata: dict[str, Any] | None = None,
        invoice_id: int | None = None,
        browser_mode: str | None = None,
    ) -> FiscalOperation:
        env = canonical_dgii_environment(environment)
        operation_key = build_operation_key(
            tenant_id=tenant_id,
            document_type=document_type,
            document_number=document_number,
            environment=env,
            payload_hash=payload_hash,
            source_system=source_system,
        )
        existing = self.db.scalar(select(FiscalOperation).where(FiscalOperation.operation_key == operation_key))
        if existing:
            return existing

        correlation_id = uuid.uuid4().hex
        operation = FiscalOperation(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            operation_id=uuid.uuid4().hex,
            operation_key=operation_key,
            correlation_id=correlation_id,
            request_id=request_id,
            environment=env,
            source_system=source_system,
            document_type=document_type,
            document_number=document_number,
            state="QUEUED",
            payload_hash=payload_hash,
            currency=currency,
            amount_total=amount_total,
            initiated_by=initiated_by,
            browser_mode=browser_mode,
            metadata_json=metadata or {},
        )
        self.db.add(operation)
        self.db.flush()
        self.record_event(operation, status="QUEUED", title="Operacion creada", stage="QUEUED", details=metadata or {})
        return operation

    def record_event(
        self,
        operation: FiscalOperation,
        *,
        status: str,
        title: str,
        message: str | None = None,
        stage: str | None = None,
        details: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        occurred_at: datetime | None = None,
    ) -> FiscalOperationEvent:
        event = FiscalOperationEvent(
            operation_fk=operation.id,
            status=status,
            title=title,
            message=message,
            stage=stage or status,
            details_json=details or {},
            duration_ms=duration_ms,
            occurred_at=occurred_at or utcnow(),
        )
        self.db.add(event)
        operation.last_transition_at = event.occurred_at
        self.db.flush()
        return event

    def transition(
        self,
        operation: FiscalOperation,
        *,
        state: str,
        title: str,
        message: str | None = None,
        stage: str | None = None,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        completed: bool | None = None,
        occurred_at: datetime | None = None,
    ) -> FiscalOperation:
        operation.state = state
        if error_code is not None:
            operation.last_error_code = error_code
        if error_message is not None:
            operation.last_error_message = error_message
        event_time = occurred_at or utcnow()
        operation.last_transition_at = event_time
        if completed is True or state in FINAL_OPERATION_STATES:
            operation.completed_at = event_time
        self.record_event(
            operation,
            status=state,
            title=title,
            message=message,
            stage=stage or state,
            details=details,
            occurred_at=event_time,
        )
        self.db.flush()
        return operation

    def link_invoice(self, operation: FiscalOperation, invoice_id: int) -> FiscalOperation:
        operation.invoice_id = invoice_id
        self.db.flush()
        return operation

    def register_dgii_attempt(
        self,
        operation: FiscalOperation,
        *,
        endpoint: str,
        request_payload_hash: str | None,
        request_headers: dict[str, Any] | None = None,
    ) -> DGIIAttempt:
        attempt_no = len(operation.dgii_attempts) + 1
        attempt = DGIIAttempt(
            operation_fk=operation.id,
            attempt_no=attempt_no,
            endpoint=endpoint,
            request_payload_hash=request_payload_hash,
            request_headers_json=request_headers or {},
            status="PENDING",
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def finish_dgii_attempt(
        self,
        attempt: DGIIAttempt,
        *,
        status: str,
        http_status: int | None = None,
        response: dict[str, Any] | None = None,
        track_id: str | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> DGIIAttempt:
        end = finished_at or utcnow()
        attempt.status = status
        attempt.http_status = http_status
        attempt.immediate_response_json = response or {}
        attempt.track_id = track_id
        attempt.error_message = error_message
        attempt.finished_at = end
        attempt.latency_ms = int((end - attempt.started_at).total_seconds() * 1000)
        self.db.flush()
        return attempt

    def register_odoo_attempt(
        self,
        operation: FiscalOperation,
        *,
        remote_model: str,
        payload: dict[str, Any],
    ) -> OdooSyncAttempt:
        attempt_no = len(operation.odoo_attempts) + 1
        attempt = OdooSyncAttempt(
            operation_fk=operation.id,
            attempt_no=attempt_no,
            remote_model=remote_model,
            payload_json=payload,
            status="PENDING",
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def finish_odoo_attempt(
        self,
        attempt: OdooSyncAttempt,
        *,
        status: str,
        response: dict[str, Any] | None = None,
        remote_record_id: str | None = None,
        remote_name: str | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> OdooSyncAttempt:
        end = finished_at or utcnow()
        attempt.status = status
        attempt.response_json = response or {}
        attempt.remote_record_id = remote_record_id
        attempt.remote_name = remote_name
        attempt.error_message = error_message
        attempt.finished_at = end
        attempt.latency_ms = int((end - attempt.started_at).total_seconds() * 1000)
        self.db.flush()
        return attempt

    def register_evidence(
        self,
        operation: FiscalOperation,
        *,
        artifact_type: str,
        file_path: str,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceArtifact:
        path = Path(file_path)
        checksum = None
        size_bytes = None
        if path.exists():
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            size_bytes = path.stat().st_size
        artifact = EvidenceArtifact(
            operation_fk=operation.id,
            artifact_type=artifact_type,
            file_path=str(path),
            content_type=content_type,
            checksum=checksum,
            size_bytes=size_bytes,
            metadata_json=metadata or {},
        )
        self.db.add(artifact)
        self.db.flush()
        return artifact

    def increment_retry(self, operation: FiscalOperation, *, reason: str) -> FiscalOperation:
        operation.retry_count += 1
        self.transition(
            operation,
            state="RETRYING",
            title="Reintento controlado",
            message=reason,
            details={"retryCount": operation.retry_count},
        )
        return operation

    def update_remote_status(self, operation: FiscalOperation, remote_status: str, *, message: str | None = None) -> FiscalOperation:
        mapped = map_remote_status(remote_status)
        operation.dgii_status = remote_status
        return self.transition(
            operation,
            state=mapped,
            title="Estado DGII actualizado",
            message=message or remote_status,
            details={"remoteStatus": remote_status},
            completed=mapped in FINAL_OPERATION_STATES,
        )

    def upsert_coverage_result(
        self,
        *,
        environment: str,
        document_type: str,
        result_status: str,
        classification: str | None = None,
        odoo_supported: str = "UNKNOWN",
        easycounting_supported: str = "UNKNOWN",
        dgii_supported: str = "UNKNOWN",
        sandbox_supported: str = "UNKNOWN",
        supports_amount_0001: str = "UNKNOWN",
        minimum_supported_amount: Decimal | None = None,
        last_operation_id: str | None = None,
        restriction_source: str | None = None,
        notes: str | None = None,
        evidence_path: str | None = None,
    ) -> ComprobanteCoverageResult:
        env = canonical_dgii_environment(environment)
        row = self.db.scalar(
            select(ComprobanteCoverageResult).where(
                ComprobanteCoverageResult.environment == env,
                ComprobanteCoverageResult.document_type == document_type,
            )
        )
        if row is None:
            row = ComprobanteCoverageResult(environment=env, document_type=document_type)
            self.db.add(row)
        row.classification = classification
        row.odoo_supported = odoo_supported
        row.easycounting_supported = easycounting_supported
        row.dgii_supported = dgii_supported
        row.sandbox_supported = sandbox_supported
        row.supports_amount_0001 = supports_amount_0001
        row.minimum_supported_amount = minimum_supported_amount
        row.last_operation_id = last_operation_id
        row.result_status = result_status
        row.restriction_source = restriction_source
        row.notes = notes
        row.evidence_path = evidence_path
        self.db.flush()
        return row
