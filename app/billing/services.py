"""Servicios de cálculo y persistencia de cargos por uso."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.billing import Plan, UsageRecord
from app.models.tenant import Tenant
from app.shared.database import get_db


class BillingError(RuntimeError):
    """Error controlado en la generación de cargos."""


@dataclass(slots=True)
class BillingContext:
    tenant: Tenant
    plan: Plan
    now: datetime


class BillingService:
    """Reglas de negocio para registrar consumo y generar reportes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _resolve_tenant(self, tenant_id: int | None = None, *, rnc: str | None = None) -> Tenant:
        tenant: Tenant | None = None
        if tenant_id is not None:
            tenant = self.db.get(Tenant, tenant_id)
        elif rnc:
            tenant = self.db.scalar(select(Tenant).where(Tenant.rnc == rnc))
        if not tenant:
            raise BillingError("No se encontró el tenant asociado al envío")
        return tenant

    def _prepare_context(self, tenant: Tenant) -> BillingContext:
        plan = tenant.plan
        if not plan:
            raise BillingError("El tenant no tiene un plan de facturación asignado")
        now = datetime.utcnow()
        return BillingContext(tenant=tenant, plan=plan, now=now)

    def _month_window(self, reference: datetime) -> tuple[datetime, datetime]:
        start = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    def _compute_charge(self, context: BillingContext, invoice_id: int | None, ecf_type: str) -> Decimal:
        start, end = self._month_window(context.now)
        registros_mes = self.db.scalar(
            select(func.count(UsageRecord.id)).where(
                UsageRecord.tenant_id == context.tenant.id,
                UsageRecord.fecha >= start,
                UsageRecord.fecha < end,
            )
        ) or 0
        # Se cobra precio_por_documento a partir del documento que excede el cupo incluido.
        if context.plan.documentos_incluidos and registros_mes < context.plan.documentos_incluidos:
            return Decimal("0")
        precio = context.plan.precio_por_documento or Decimal("0")
        return Decimal(str(precio))

    def record_usage(
        self,
        *,
        tenant_id: int | None = None,
        rnc: str | None = None,
        ecf_type: str,
        track_id: str | None = None,
        invoice_id: int | None = None,
    ) -> UsageRecord:
        tenant = self._resolve_tenant(tenant_id, rnc=rnc)
        context = self._prepare_context(tenant)
        monto = self._compute_charge(context, invoice_id, ecf_type)
        record = UsageRecord(
            tenant_id=tenant.id,
            plan_id=context.plan.id,
            invoice_id=invoice_id,
            ecf_type=ecf_type,
            track_id=track_id,
            monto_cargado=monto,
            fecha=context.now,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def record_usage_for_rnc(
        self,
        *,
        rnc: str,
        ecf_type: str,
        track_id: str | None = None,
        invoice_id: int | None = None,
    ) -> UsageRecord:
        return self.record_usage(rnc=rnc, ecf_type=ecf_type, track_id=track_id, invoice_id=invoice_id)


def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    return BillingService(db)


