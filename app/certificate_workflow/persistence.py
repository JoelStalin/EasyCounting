from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.certificate_workflow.models import IntakePayload, PrecheckResult, WorkflowStatus
from app.models.certificate_workflow import (
    CertificateValidation,
    PscRequest,
    WorkflowEvent,
    WorkflowExecution,
    WorkflowReminder,
    WorkflowStepLog,
)


def _payload_dict(payload: IntakePayload) -> dict:
    return {
        "rnc": payload.rnc,
        "razon_social": payload.razon_social,
        "tipo_contribuyente": payload.tipo_contribuyente,
        "delegado_nombre": payload.delegado_nombre,
        "delegado_identificacion": payload.delegado_identificacion,
        "delegado_correo": payload.delegado_correo,
        "delegado_telefono": payload.delegado_telefono,
        "delegado_cargo": payload.delegado_cargo,
        "psc_preferida": payload.psc_preferida,
        "usa_facturador_gratuito": payload.usa_facturador_gratuito,
        "ofv_habilitada": payload.ofv_habilitada,
        "alta_ncf_habilitada": payload.alta_ncf_habilitada,
        "responsable_ti": payload.responsable_ti,
        "responsable_fiscal": payload.responsable_fiscal,
        "ambiente_objetivo": payload.ambiente_objetivo,
        "stack_tecnico": payload.stack_tecnico,
        "repositorio": payload.repositorio,
        "secret_manager": payload.secret_manager,
        "metadata": payload.metadata,
    }


class CertificateWorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(self, *, case_id: str, payload: IntakePayload, status_value: WorkflowStatus) -> PscRequest:
        row = PscRequest(
            case_id=case_id,
            rnc=payload.rnc,
            razon_social=payload.razon_social,
            delegado_nombre=payload.delegado_nombre,
            delegado_identificacion=payload.delegado_identificacion,
            psc_code=payload.psc_preferida,
            status=status_value.value,
            owner_email=payload.responsable_fiscal or payload.delegado_correo or None,
            payload_json=_payload_dict(payload),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def set_status(self, case_id: str, status_value: WorkflowStatus) -> PscRequest:
        row = self.get_request(case_id)
        row.status = status_value.value
        self.db.flush()
        return row

    def transition_status(self, case_id: str, *, target_status: WorkflowStatus, note: str | None = None) -> PscRequest:
        row = self.get_request(case_id)
        row.status = target_status.value
        self.db.flush()
        self.append_event(
            request_row=row,
            event_type=target_status.value,
            payload={"note": note or ""},
        )
        return row

    def append_event(self, *, request_row: PscRequest, event_type: str, payload: dict) -> WorkflowEvent:
        event = WorkflowEvent(
            psc_request_id=request_row.id,
            case_id=request_row.case_id,
            event_type=event_type,
            event_payload=payload,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def get_request(self, case_id: str) -> PscRequest:
        row = self.db.scalar(select(PscRequest).where(PscRequest.case_id == case_id).limit(1))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case_id no encontrado")
        return row

    def list_events(self, case_id: str) -> list[WorkflowEvent]:
        request_row = self.get_request(case_id)
        return list(
            self.db.scalars(
                select(WorkflowEvent).where(WorkflowEvent.psc_request_id == request_row.id).order_by(WorkflowEvent.id.asc())
            ).all()
        )

    def create_validation(
        self,
        *,
        case_id: str,
        file_name: str,
        sha256: str,
        subject: str | None,
        serial_number: str | None,
        not_before: datetime | None,
        not_after: datetime | None,
        has_private_key: bool,
        password_ok: bool,
        valid: bool,
        error: str | None,
    ) -> CertificateValidation:
        request_row = self.get_request(case_id)
        row = CertificateValidation(
            psc_request_id=request_row.id,
            case_id=request_row.case_id,
            file_name=file_name,
            sha256=sha256,
            subject=subject,
            serial_number=serial_number,
            not_before=not_before,
            not_after=not_after,
            has_private_key=has_private_key,
            password_ok=password_ok,
            valid=valid,
            error=error,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def latest_validation(self, case_id: str) -> CertificateValidation | None:
        request_row = self.get_request(case_id)
        return self.db.scalar(
            select(CertificateValidation)
            .where(CertificateValidation.psc_request_id == request_row.id)
            .order_by(CertificateValidation.id.desc())
            .limit(1)
        )

    def schedule_reminder(self, *, case_id: str, title: str, hours: int, metadata: dict | None = None) -> WorkflowReminder:
        request_row = self.get_request(case_id)
        reminder = WorkflowReminder(
            psc_request_id=request_row.id,
            case_id=request_row.case_id,
            status="PENDING",
            title=title,
            due_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=hours),
            metadata_json=metadata or {},
        )
        self.db.add(reminder)
        self.db.flush()
        self.append_event(
            request_row=request_row,
            event_type="REMINDER_SCHEDULED",
            payload={"title": title, "hours": hours},
        )
        return reminder

    def due_reminders(self, *, limit: int = 50) -> list[WorkflowReminder]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return list(
            self.db.scalars(
                select(WorkflowReminder)
                .where(WorkflowReminder.status == "PENDING", WorkflowReminder.due_at <= now)
                .order_by(WorkflowReminder.due_at.asc())
                .limit(limit)
            ).all()
        )

    def resolve_reminder(self, reminder_id: int) -> WorkflowReminder:
        reminder = self.db.get(WorkflowReminder, reminder_id)
        if reminder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder no encontrado")
        reminder.status = "RESOLVED"
        reminder.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.flush()
        request_row = self.get_request(reminder.case_id)
        self.append_event(
            request_row=request_row,
            event_type="REMINDER_RESOLVED",
            payload={"reminder_id": reminder_id, "title": reminder.title},
        )
        return reminder

    def set_secret_ref(self, *, case_id: str, secret_ref: str) -> PscRequest:
        row = self.get_request(case_id)
        row.secret_ref = secret_ref
        row.status = WorkflowStatus.SECRET_STORED.value
        self.db.flush()
        self.append_event(
            request_row=row,
            event_type=WorkflowStatus.SECRET_STORED.value,
            payload={"secret_ref": secret_ref},
        )
        return row

    def list_requests_by_status(self, statuses: list[WorkflowStatus], *, limit: int = 50) -> list[PscRequest]:
        status_values = [item.value for item in statuses]
        return list(
            self.db.scalars(
                select(PscRequest)
                .where(PscRequest.status.in_(status_values))
                .order_by(PscRequest.updated_at.asc(), PscRequest.id.asc())
                .limit(limit)
            ).all()
        )

    def start_execution(
        self,
        *,
        case_id: str,
        current_step: str = "INTAKE_RECEIVED",
        status_value: str = "RUNNING",
    ) -> WorkflowExecution:
        request_row = self.get_request(case_id)
        prev = self.latest_execution(case_id)
        attempt = 1 if prev is None else prev.attempt + 1
        execution_id = f"exec-{case_id}-{attempt}-{uuid.uuid4().hex[:8]}"
        resume_token = uuid.uuid4().hex
        row = WorkflowExecution(
            psc_request_id=request_row.id,
            case_id=request_row.case_id,
            execution_id=execution_id,
            current_step=current_step,
            status=status_value,
            last_success_step=None,
            resume_token=resume_token,
            attempt=attempt,
            ended_at=None,
        )
        self.db.add(row)
        self.db.flush()
        self.append_event(
            request_row=request_row,
            event_type="WORKFLOW_EXECUTION_STARTED",
            payload={"execution_id": execution_id, "attempt": attempt, "step": current_step},
        )
        return row

    def latest_execution(self, case_id: str) -> WorkflowExecution | None:
        request_row = self.get_request(case_id)
        return self.db.scalar(
            select(WorkflowExecution)
            .where(WorkflowExecution.psc_request_id == request_row.id)
            .order_by(WorkflowExecution.id.desc())
            .limit(1)
        )

    def get_execution(self, execution_id: str) -> WorkflowExecution:
        row = self.db.scalar(select(WorkflowExecution).where(WorkflowExecution.execution_id == execution_id).limit(1))
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="execution_id no encontrado")
        return row

    def log_step(
        self,
        *,
        execution_id: str,
        step: str,
        action: str,
        result: str,
        error_code: str | None = None,
        error_message: str | None = None,
        screenshot_path: str | None = None,
        artifact_path: str | None = None,
        details: dict | None = None,
    ) -> WorkflowStepLog:
        execution = self.get_execution(execution_id)
        log = WorkflowStepLog(
            workflow_execution_id=execution.id,
            execution_id=execution.execution_id,
            step=step,
            action=action,
            result=result,
            error_code=error_code,
            error_message=error_message,
            screenshot_path=screenshot_path,
            artifact_path=artifact_path,
            details_json=details or {},
        )
        self.db.add(log)
        if result.upper() in {"OK", "SUCCESS"}:
            execution.last_success_step = step
            execution.current_step = step
            execution.status = "RUNNING"
        elif result.upper() in {"FAILED_BLOCKED", "BLOCKED"}:
            execution.current_step = step
            execution.status = "FAILED_BLOCKED"
        elif result.upper() in {"FAILED_RETRYABLE", "RETRYABLE"}:
            execution.current_step = step
            execution.status = "FAILED_RETRYABLE"
        elif result.upper() in {"DONE", "COMPLETED"}:
            execution.current_step = step
            execution.status = "COMPLETED"
            execution.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.flush()
        request_row = self.get_request(execution.case_id)
        self.append_event(
            request_row=request_row,
            event_type="WORKFLOW_STEP_LOGGED",
            payload={
                "execution_id": execution.execution_id,
                "step": step,
                "action": action,
                "result": result,
                "error_code": error_code,
            },
        )
        return log

    def list_execution_logs(self, execution_id: str, *, limit: int = 200) -> list[WorkflowStepLog]:
        execution = self.get_execution(execution_id)
        return list(
            self.db.scalars(
                select(WorkflowStepLog)
                .where(WorkflowStepLog.workflow_execution_id == execution.id)
                .order_by(WorkflowStepLog.id.desc())
                .limit(limit)
            ).all()
        )

    def resume_latest_execution(self, case_id: str) -> WorkflowExecution:
        execution = self.latest_execution(case_id)
        if execution is None:
            return self.start_execution(case_id=case_id, current_step="INTAKE_RECEIVED", status_value="RUNNING")
        if execution.status in {"COMPLETED"}:
            return self.start_execution(
                case_id=case_id,
                current_step=execution.last_success_step or execution.current_step or "INTAKE_RECEIVED",
                status_value="RUNNING",
            )
        execution.status = "RUNNING"
        execution.current_step = execution.last_success_step or execution.current_step or "INTAKE_RECEIVED"
        execution.resume_token = uuid.uuid4().hex
        execution.ended_at = None
        self.db.flush()
        request_row = self.get_request(case_id)
        self.append_event(
            request_row=request_row,
            event_type="WORKFLOW_EXECUTION_RESUMED",
            payload={
                "execution_id": execution.execution_id,
                "current_step": execution.current_step,
                "last_success_step": execution.last_success_step,
            },
        )
        return execution
