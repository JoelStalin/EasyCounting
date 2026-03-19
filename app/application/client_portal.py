"""Application services for client portal operations."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.billing import Plan, UsageRecord
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.portal_client.schemas import (
    InvoiceDetailResponse,
    InvoiceListItem,
    InvoiceListResponse,
    PlanPublic,
    TenantPlanSummary,
    UsageInvoiceItem,
    UsageListResponse,
    UsageSummary,
)


def _month_range(month: datetime) -> tuple[datetime, datetime]:
    start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def _next_month_start(reference: datetime) -> datetime:
    _start, end = _month_range(reference)
    return end


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


def _apply_pending_plan_if_due(db: Session, tenant: Tenant) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if tenant.pending_plan_id and tenant.plan_change_effective_at and tenant.plan_change_effective_at <= now:
        pending_plan = db.get(Plan, tenant.pending_plan_id)
        if pending_plan:
            tenant.plan = pending_plan
            tenant.plan_id = pending_plan.id
        tenant.pending_plan_id = None
        tenant.plan_change_requested_at = None
        tenant.plan_change_effective_at = None
        db.flush()


class ClientPortalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_plans(self) -> list[PlanPublic]:
        plans = self.db.scalars(select(Plan).order_by(Plan.name)).all()
        return [PlanPublic.model_validate(plan, from_attributes=True) for plan in plans]

    def get_plan_summary(self, tenant_id: int) -> TenantPlanSummary:
        tenant = _get_tenant_or_404(self.db, tenant_id)
        _apply_pending_plan_if_due(self.db, tenant)
        current_plan = tenant.plan
        pending_plan = self.db.get(Plan, tenant.pending_plan_id) if tenant.pending_plan_id else None
        return TenantPlanSummary(
            tenant_id=tenant.id,
            current_plan=PlanPublic.model_validate(current_plan, from_attributes=True) if current_plan else None,
            pending_plan=PlanPublic.model_validate(pending_plan, from_attributes=True) if pending_plan else None,
            pending_effective_at=tenant.plan_change_effective_at,
            pending_requested_at=tenant.plan_change_requested_at,
        )

    def request_plan_change(self, tenant_id: int, plan_id: int) -> TenantPlanSummary:
        tenant = _get_tenant_or_404(self.db, tenant_id)
        _apply_pending_plan_if_due(self.db, tenant)
        plan = self.db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if tenant.plan_id is None:
            tenant.plan = plan
            tenant.plan_id = plan.id
            tenant.pending_plan_id = None
            tenant.plan_change_requested_at = None
            tenant.plan_change_effective_at = None
        elif tenant.plan_id == plan.id and tenant.pending_plan_id is None:
            pass
        else:
            tenant.pending_plan_id = plan.id
            tenant.plan_change_requested_at = now
            tenant.plan_change_effective_at = _next_month_start(now)

        self.db.flush()
        pending_plan = self.db.get(Plan, tenant.pending_plan_id) if tenant.pending_plan_id else None
        return TenantPlanSummary(
            tenant_id=tenant.id,
            current_plan=PlanPublic.model_validate(tenant.plan, from_attributes=True) if tenant.plan else None,
            pending_plan=PlanPublic.model_validate(pending_plan, from_attributes=True) if pending_plan else None,
            pending_effective_at=tenant.plan_change_effective_at,
            pending_requested_at=tenant.plan_change_requested_at,
        )

    def usage_summary(
        self,
        *,
        tenant_id: int,
        month: str | None,
        page: int,
        size: int,
    ) -> UsageListResponse:
        tenant = _get_tenant_or_404(self.db, tenant_id)
        _apply_pending_plan_if_due(self.db, tenant)
        if month:
            try:
                period = datetime.strptime(month, "%Y-%m")
            except ValueError as exc:  # pragma: no cover - validado por regex
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de mes invalido") from exc
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            period = datetime(now.year, now.month, 1)
            month = period.strftime("%Y-%m")

        start, end = _month_range(period)

        total_used = self.db.scalar(
            select(func.count(UsageRecord.id)).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.fecha >= start,
                UsageRecord.fecha < end,
            )
        ) or 0

        total_amount = self.db.scalar(
            select(func.coalesce(func.sum(UsageRecord.monto_cargado), 0)).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.fecha >= start,
                UsageRecord.fecha < end,
            )
        ) or Decimal("0")

        included = int(tenant.plan.documentos_incluidos) if tenant.plan else 0
        remaining = max(included - int(total_used), 0)

        base_query = (
            select(UsageRecord, Invoice)
            .join(Invoice, UsageRecord.invoice_id == Invoice.id, isouter=True)
            .where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.fecha >= start,
                UsageRecord.fecha < end,
            )
        )

        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        stmt = base_query.order_by(UsageRecord.fecha.desc()).offset((page - 1) * size).limit(size)
        rows = self.db.execute(stmt).all()

        items: list[UsageInvoiceItem] = []
        for usage, invoice in rows:
            items.append(
                UsageInvoiceItem(
                    usage_id=usage.id,
                    invoice_id=usage.invoice_id,
                    encf=invoice.encf if invoice else None,
                    tipo_ecf=invoice.tipo_ecf if invoice else None,
                    estado_dgii=invoice.estado_dgii if invoice else None,
                    total=Decimal(str(invoice.total)) if invoice else None,
                    monto_cargado=Decimal(str(usage.monto_cargado)),
                    fecha_emision=invoice.fecha_emision if invoice else None,
                    fecha_uso=usage.fecha,
                )
            )

        summary = UsageSummary(
            month=month or period.strftime("%Y-%m"),
            total_used=int(total_used),
            included_documents=included,
            remaining_documents=remaining,
            total_amount=Decimal(str(total_amount)),
        )

        return UsageListResponse(summary=summary, items=items, total=int(total), page=page, size=size)

    def list_invoices(
        self,
        *,
        tenant_id: int,
        page: int,
        size: int,
        estado_dgii: Optional[str],
        encf: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> InvoiceListResponse:
        base = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if estado_dgii:
            base = base.where(Invoice.estado_dgii == estado_dgii)
        if encf:
            base = base.where(Invoice.encf == encf)
        if date_from is not None:
            base = base.where(Invoice.fecha_emision >= date_from)
        if date_to is not None:
            base = base.where(Invoice.fecha_emision < date_to)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        stmt = base.order_by(Invoice.fecha_emision.desc()).offset((page - 1) * size).limit(size)
        rows = self.db.scalars(stmt).all()

        items = [
            InvoiceListItem(
                id=invoice.id,
                encf=invoice.encf,
                tipo_ecf=invoice.tipo_ecf,
                estado_dgii=invoice.estado_dgii,
                track_id=invoice.track_id,
                total=Decimal(str(invoice.total)),
                fecha_emision=invoice.fecha_emision,
            )
            for invoice in rows
        ]

        return InvoiceListResponse(items=items, total=int(total), page=page, size=size)

    def get_invoice_detail(self, *, tenant_id: int, invoice_id: int) -> InvoiceDetailResponse:
        invoice = self.db.get(Invoice, invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")

        return InvoiceDetailResponse(
            id=invoice.id,
            encf=invoice.encf,
            tipo_ecf=invoice.tipo_ecf,
            estado_dgii=invoice.estado_dgii,
            track_id=invoice.track_id,
            total=Decimal(str(invoice.total)),
            fecha_emision=invoice.fecha_emision,
            xml_path=invoice.xml_path,
            xml_hash=invoice.xml_hash,
            codigo_seguridad=invoice.codigo_seguridad,
            contabilizado=bool(invoice.contabilizado),
            accounted_at=invoice.accounted_at,
            asiento_referencia=invoice.asiento_referencia,
        )
