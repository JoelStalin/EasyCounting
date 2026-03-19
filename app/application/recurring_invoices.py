from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.invoice import Invoice
from app.models.recurring_invoice import RecurringInvoiceExecution, RecurringInvoiceSchedule
from app.models.tenant import Tenant
from app.recurring_invoices.schemas import (
    RecurringInvoiceExecutionItem,
    RecurringInvoiceRunSummary,
    RecurringInvoiceScheduleCreateRequest,
    RecurringInvoiceScheduleItem,
    RecurringInvoiceScheduleUpdateRequest,
)
from app.shared.storage import storage
from app.shared.time import utcnow


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def _add_month(reference: datetime) -> datetime:
    year = reference.year + (1 if reference.month == 12 else 0)
    month = 1 if reference.month == 12 else reference.month + 1
    day = min(reference.day, monthrange(year, month)[1])
    return reference.replace(year=year, month=month, day=day)


class RecurringInvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_schedules(self, *, tenant_id: int) -> list[RecurringInvoiceScheduleItem]:
        schedules = self.db.scalars(
            select(RecurringInvoiceSchedule)
            .where(RecurringInvoiceSchedule.tenant_id == tenant_id)
            .options(selectinload(RecurringInvoiceSchedule.executions))
            .order_by(RecurringInvoiceSchedule.created_at.desc())
        ).all()
        return [self._serialize_schedule(item) for item in schedules]

    def create_schedule(
        self,
        *,
        tenant_id: int,
        created_by_user_id: int | None,
        payload: RecurringInvoiceScheduleCreateRequest,
    ) -> RecurringInvoiceScheduleItem:
        tenant = self._get_tenant(tenant_id)
        self._assert_can_schedule(tenant)
        self._validate_payload(payload)

        schedule = RecurringInvoiceSchedule(
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            name=payload.name.strip(),
            status="active",
            frequency=payload.frequency,
            custom_interval_days=payload.custom_interval_days,
            start_at=_normalize_dt(payload.start_at),
            end_at=_normalize_dt(payload.end_at) if payload.end_at else None,
            next_run_at=_normalize_dt(payload.start_at),
            last_run_at=None,
            tipo_ecf=payload.tipo_ecf,
            rnc_receptor=payload.rnc_receptor,
            total=float(payload.total),
            notes=(payload.notes or "").strip() or None,
        )
        self.db.add(schedule)
        self.db.flush()
        self.db.refresh(schedule)
        return self._serialize_schedule(schedule)

    def update_schedule(
        self,
        *,
        tenant_id: int,
        schedule_id: int,
        payload: RecurringInvoiceScheduleUpdateRequest,
    ) -> RecurringInvoiceScheduleItem:
        schedule = self._get_schedule(tenant_id=tenant_id, schedule_id=schedule_id)
        self._assert_can_schedule(self._get_tenant(tenant_id))
        self._validate_payload(payload)

        schedule.name = payload.name.strip()
        schedule.frequency = payload.frequency
        schedule.custom_interval_days = payload.custom_interval_days
        schedule.start_at = _normalize_dt(payload.start_at)
        schedule.end_at = _normalize_dt(payload.end_at) if payload.end_at else None
        schedule.tipo_ecf = payload.tipo_ecf
        schedule.rnc_receptor = payload.rnc_receptor
        schedule.total = float(payload.total)
        schedule.notes = (payload.notes or "").strip() or None
        if payload.status:
            schedule.status = payload.status
        if schedule.status == "active":
            schedule.next_run_at = schedule.next_run_at or schedule.start_at
        elif schedule.status in {"completed", "cancelled"}:
            schedule.next_run_at = None
        self.db.flush()
        self.db.refresh(schedule)
        return self._serialize_schedule(schedule)

    def pause_schedule(self, *, tenant_id: int, schedule_id: int) -> RecurringInvoiceScheduleItem:
        schedule = self._get_schedule(tenant_id=tenant_id, schedule_id=schedule_id)
        schedule.status = "paused"
        self.db.flush()
        return self._serialize_schedule(schedule)

    def resume_schedule(self, *, tenant_id: int, schedule_id: int) -> RecurringInvoiceScheduleItem:
        tenant = self._get_tenant(tenant_id)
        self._assert_can_schedule(tenant)
        schedule = self._get_schedule(tenant_id=tenant_id, schedule_id=schedule_id)
        schedule.status = "active"
        if schedule.next_run_at is None:
            schedule.next_run_at = schedule.start_at if schedule.last_run_at is None else self._compute_next_run(schedule.last_run_at, schedule)
        self.db.flush()
        return self._serialize_schedule(schedule)

    def run_due_schedules(self, *, tenant_id: int | None = None, now: datetime | None = None) -> RecurringInvoiceRunSummary:
        run_at = now or utcnow()
        if tenant_id is not None:
            self._assert_can_schedule(self._get_tenant(tenant_id))
        stmt = (
            select(RecurringInvoiceSchedule)
            .where(
                RecurringInvoiceSchedule.status == "active",
                RecurringInvoiceSchedule.next_run_at.is_not(None),
                RecurringInvoiceSchedule.next_run_at <= run_at,
            )
            .options(selectinload(RecurringInvoiceSchedule.executions))
            .order_by(RecurringInvoiceSchedule.next_run_at.asc())
        )
        if tenant_id is not None:
            stmt = stmt.where(RecurringInvoiceSchedule.tenant_id == tenant_id)
        schedules = self.db.scalars(stmt).all()

        processed = generated = failed = 0
        changed: list[RecurringInvoiceSchedule] = []
        for schedule in schedules:
            processed += 1
            success = self._run_schedule_due_occurrences(schedule, now=run_at)
            if success:
                generated += 1
            else:
                failed += 1
            changed.append(schedule)

        self.db.flush()
        return RecurringInvoiceRunSummary(
            processed=processed,
            generated=generated,
            failed=failed,
            schedules=[self._serialize_schedule(item) for item in changed],
        )

    def _run_schedule_due_occurrences(self, schedule: RecurringInvoiceSchedule, *, now: datetime) -> bool:
        tenant = self._get_tenant(schedule.tenant_id)
        blocked = self._get_schedule_block(tenant)
        if blocked is not None:
            self._pause_blocked_schedule(
                schedule=schedule,
                scheduled_for=schedule.next_run_at or now,
                detail=blocked[1],
            )
            return False
        success = True
        due_at = schedule.next_run_at
        while due_at is not None and due_at <= now and schedule.status == "active":
            if schedule.end_at and due_at > schedule.end_at:
                schedule.status = "completed"
                schedule.next_run_at = None
                break

            existing_execution = self.db.scalar(
                select(RecurringInvoiceExecution).where(
                    RecurringInvoiceExecution.schedule_id == schedule.id,
                    RecurringInvoiceExecution.scheduled_for == due_at,
                )
            )
            if existing_execution:
                schedule.last_run_at = due_at
                schedule.next_run_at = self._compute_next_or_finish(schedule=schedule, reference=due_at)
                due_at = schedule.next_run_at
                continue

            try:
                invoice = self._materialize_invoice(schedule=schedule, scheduled_for=due_at)
                execution = RecurringInvoiceExecution(
                    schedule_id=schedule.id,
                    tenant_id=schedule.tenant_id,
                    invoice_id=invoice.id,
                    scheduled_for=due_at,
                    executed_at=utcnow(),
                    status="generated",
                )
                self.db.add(execution)
                schedule.last_generated_invoice_id = invoice.id
                schedule.last_run_at = due_at
                schedule.next_run_at = self._compute_next_or_finish(schedule=schedule, reference=due_at)
                due_at = schedule.next_run_at
            except Exception as exc:  # noqa: BLE001
                self.db.add(
                    RecurringInvoiceExecution(
                        schedule_id=schedule.id,
                        tenant_id=schedule.tenant_id,
                        invoice_id=None,
                        scheduled_for=due_at,
                        executed_at=utcnow(),
                        status="failed",
                        error_message=str(exc)[:512],
                    )
                )
                schedule.last_run_at = due_at
                schedule.next_run_at = self._compute_next_or_finish(schedule=schedule, reference=due_at)
                due_at = schedule.next_run_at
                success = False
        return success

    def _pause_blocked_schedule(self, *, schedule: RecurringInvoiceSchedule, scheduled_for: datetime, detail: str) -> None:
        schedule.status = "paused"
        self.db.add(
            RecurringInvoiceExecution(
                schedule_id=schedule.id,
                tenant_id=schedule.tenant_id,
                invoice_id=None,
                scheduled_for=scheduled_for,
                executed_at=utcnow(),
                status="failed",
                error_message=detail[:512],
            )
        )

    def _materialize_invoice(self, *, schedule: RecurringInvoiceSchedule, scheduled_for: datetime) -> Invoice:
        encf = self._generate_encf(schedule, scheduled_for)
        track_id = f"rec-{schedule.id}-{scheduled_for:%Y%m%d%H%M%S}"
        relative_path = f"recurring/{schedule.tenant_id}/{schedule.id}/{track_id}.json"
        storage.store_json(
            relative_path,
            {
                "source": "recurring_invoice_schedule",
                "schedule_id": schedule.id,
                "scheduled_for": scheduled_for.isoformat(),
                "encf": encf,
                "tipo_ecf": schedule.tipo_ecf,
                "rnc_receptor": schedule.rnc_receptor,
                "total": str(schedule.total),
                "notes": schedule.notes,
            },
        )
        xml_hash = storage.compute_hash(relative_path)
        invoice = Invoice(
            tenant_id=schedule.tenant_id,
            encf=encf,
            tipo_ecf=schedule.tipo_ecf,
            rnc_receptor=schedule.rnc_receptor,
            xml_path=relative_path,
            xml_hash=xml_hash,
            estado_dgii="PROGRAMADA_GENERADA",
            track_id=track_id,
            codigo_seguridad=None,
            total=float(Decimal(str(schedule.total))),
            fecha_emision=scheduled_for,
        )
        self.db.add(invoice)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se pudo materializar la factura recurrente") from exc
        return invoice

    def _compute_next_or_finish(self, *, schedule: RecurringInvoiceSchedule, reference: datetime) -> datetime | None:
        next_run = self._compute_next_run(reference, schedule)
        if schedule.end_at and next_run > schedule.end_at:
            schedule.status = "completed"
            return None
        return next_run

    @staticmethod
    def _compute_next_run(reference: datetime, schedule: RecurringInvoiceSchedule) -> datetime:
        if schedule.frequency == "daily":
            return reference + timedelta(days=1)
        if schedule.frequency == "biweekly":
            return reference + timedelta(days=14)
        if schedule.frequency == "monthly":
            return _add_month(reference)
        interval = schedule.custom_interval_days or 1
        return reference + timedelta(days=interval)

    @staticmethod
    def _generate_encf(schedule: RecurringInvoiceSchedule, scheduled_for: datetime) -> str:
        return f"R{schedule.id:04d}{scheduled_for:%y%m%d%H%M%S}"

    def _get_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        return tenant

    def _get_schedule(self, *, tenant_id: int, schedule_id: int) -> RecurringInvoiceSchedule:
        schedule = self.db.get(RecurringInvoiceSchedule, schedule_id)
        if not schedule or schedule.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura recurrente no encontrada")
        return schedule

    @staticmethod
    def _get_schedule_block(tenant: Tenant) -> tuple[int, str] | None:
        if tenant.onboarding_status != "completed":
            return (
                status.HTTP_409_CONFLICT,
                "El tenant debe completar su setup fiscal antes de programar facturas recurrentes",
            )
        if not tenant.plan or not bool(tenant.plan.includes_recurring_invoices):
            return (
                status.HTTP_403_FORBIDDEN,
                "Las facturas recurrentes estan disponibles desde el plan Profesional (Pro).",
            )
        return None

    @classmethod
    def _assert_can_schedule(cls, tenant: Tenant) -> None:
        blocked = cls._get_schedule_block(tenant)
        if blocked is None:
            return
        raise HTTPException(
            status_code=blocked[0],
            detail=blocked[1],
        )

    @staticmethod
    def _validate_payload(payload: RecurringInvoiceScheduleCreateRequest | RecurringInvoiceScheduleUpdateRequest) -> None:
        start_at = _normalize_dt(payload.start_at)
        end_at = _normalize_dt(payload.end_at) if payload.end_at else None
        if end_at and end_at < start_at:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El rango de fin no puede ser menor que el inicio")
        if payload.frequency == "custom" and not payload.custom_interval_days:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Debes indicar customIntervalDays para frecuencia personalizada")
        if payload.frequency != "custom" and payload.custom_interval_days is not None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="customIntervalDays solo aplica a frecuencia personalizada")

    def _serialize_schedule(self, schedule: RecurringInvoiceSchedule) -> RecurringInvoiceScheduleItem:
        executions = sorted(schedule.executions, key=lambda item: item.executed_at, reverse=True)[:5]
        return RecurringInvoiceScheduleItem(
            id=schedule.id,
            name=schedule.name,
            status=schedule.status,  # type: ignore[arg-type]
            frequency=schedule.frequency,  # type: ignore[arg-type]
            customIntervalDays=schedule.custom_interval_days,
            startAt=schedule.start_at,
            endAt=schedule.end_at,
            nextRunAt=schedule.next_run_at,
            lastRunAt=schedule.last_run_at,
            tipoEcf=schedule.tipo_ecf,
            rncReceptor=schedule.rnc_receptor,
            total=Decimal(str(schedule.total)),
            notes=schedule.notes,
            lastGeneratedInvoiceId=schedule.last_generated_invoice_id,
            createdAt=schedule.created_at,
            updatedAt=schedule.updated_at,
            executions=[
                RecurringInvoiceExecutionItem(
                    id=item.id,
                    invoiceId=item.invoice_id,
                    scheduledFor=item.scheduled_for,
                    executedAt=item.executed_at,
                    status=item.status,
                    errorMessage=item.error_message,
                )
                for item in executions
            ],
        )


def run_due_recurring_invoices_batch(*, tenant_id: int | None = None) -> RecurringInvoiceRunSummary:
    from app.shared.database import session_scope

    with session_scope() as session:
        return RecurringInvoiceService(session).run_due_schedules(tenant_id=tenant_id)
