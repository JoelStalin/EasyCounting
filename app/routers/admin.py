"""Endpoints administrativos para contabilidad y configuración de empresas."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin.schemas import (
    AuditLogItem,
    BillingSummaryItem,
    BillingSummaryResponse,
    DashboardKpisResponse,
    InvoiceDetailResponse,
    InvoiceListItem,
    InvoiceListResponse,
    LedgerEntryCreate,
    LedgerEntryItem,
    LedgerPaginatedResponse,
    LedgerSummaryResponse,
    LedgerTotals,
    LedgerMonthlyStat,
    LedgerStatusBreakdown,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    TenantPlanAssignment,
    TenantPlanResponse,
    TenantSettingsPayload,
    TenantSettingsResponse,
    TenantCreate,
    TenantItem,
    TenantUpdate,
    PlatformUserItem,
)
from app.infra.settings import settings as app_settings
from app.models.billing import Plan, UsageRecord
from app.models.accounting import InvoiceLedgerEntry, TenantSettings
from app.models.audit import AuditLog
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.models.user import User
from app.shared.database import get_db
from app.shared.security import decode_jwt
from app.portal_admin.reports import billing_summary


def _require_platform_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if app_settings.environment in {"test", "testing"}:
        request.state.platform_payload = {}
        return {}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization inválido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc
    role = payload.get("role")
    if not isinstance(role, str) or not role.startswith("platform_"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a plataforma")
    request.state.platform_payload = payload
    return payload


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(_require_platform_user)])


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


def _get_settings(db: Session, tenant_id: int) -> TenantSettings:
    tenant_settings = db.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
    if tenant_settings:
        return tenant_settings
    tenant_settings = TenantSettings(tenant_id=tenant_id)
    db.add(tenant_settings)
    db.flush()
    return tenant_settings


def _actor_from_payload(db: Session, payload: dict) -> str:
    subject = payload.get("sub")
    role = payload.get("role")
    try:
        user_id = int(subject) if subject is not None else None
    except (TypeError, ValueError):
        user_id = None
    if user_id is not None:
        user = db.get(User, user_id)
        if user:
            return user.email
    if isinstance(subject, str) and subject:
        if isinstance(role, str) and role:
            return f"user:{subject}:{role}"
        return f"user:{subject}"
    return "unknown"


def _append_audit_log(
    db: Session,
    *,
    tenant_id: int,
    payload: dict,
    action: str,
    resource: str,
) -> None:
    last = db.scalar(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.id.desc())
        .limit(1)
    )
    hash_prev = last.hash_curr if last else "0" * 64
    actor = _actor_from_payload(db, payload)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    raw = f"{tenant_id}|{actor}|{action}|{resource}|{hash_prev}|{now.isoformat()}"
    hash_curr = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            resource=resource,
            hash_prev=hash_prev,
            hash_curr=hash_curr,
            created_at=now,
            updated_at=now,
        )
    )


def _platform_payload(request: Request | None) -> dict:
    if request is None:
        return {}
    return getattr(request.state, "platform_payload", {})


def _month_range(month: datetime) -> tuple[datetime, datetime]:
    start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


@router.get("/tenants", response_model=List[TenantItem])
def list_tenants(db: Session = Depends(get_db)) -> List[TenantItem]:
    tenants = db.scalars(select(Tenant).order_by(Tenant.id.desc())).all()
    return [
        TenantItem(
            id=tenant.id,
            name=tenant.name,
            rnc=tenant.rnc,
            env=tenant.env,
            status="Activa",
        )
        for tenant in tenants
    ]


@router.post("/tenants", response_model=TenantItem, status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: Request,
    payload: TenantCreate,
    db: Session = Depends(get_db),
) -> TenantItem:
    platform_payload = _platform_payload(request)
    existing = db.scalar(select(Tenant).where(Tenant.rnc == payload.rnc))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RNC ya registrado")

    default_plan = db.scalar(select(Plan).where(Plan.name == "Emprendedor").limit(1))

    tenant = Tenant(
        name=payload.name,
        rnc=payload.rnc,
        env=payload.env,
        plan_id=default_plan.id if default_plan else None,
        dgii_base_ecf=str(payload.dgii_base_ecf or app_settings.dgii_recepcion_base_url),
        dgii_base_fc=str(payload.dgii_base_fc or app_settings.dgii_recepcion_fc_base_url),
    )
    db.add(tenant)
    db.flush()
    _append_audit_log(
        db,
        tenant_id=tenant.id,
        payload=platform_payload,
        action="TENANT_CREATED",
        resource=f"tenant:{tenant.id}",
    )
    return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")


@router.get("/dashboard/kpis", response_model=DashboardKpisResponse)
def dashboard_kpis(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DashboardKpisResponse:
    if month:
        try:
            period = datetime.strptime(month, "%Y-%m")
        except ValueError as exc:  # pragma: no cover - validado por regex
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de mes inválido") from exc
    else:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        period = datetime(now.year, now.month, 1)
        month = period.strftime("%Y-%m")

    start, end = _month_range(period)

    companies_active = db.scalar(select(func.count()).select_from(Tenant)) or 0
    invoices_month = (
        db.scalar(
            select(func.count()).where(
                Invoice.fecha_emision >= start,
                Invoice.fecha_emision < end,
            )
        )
        or 0
    )
    invoices_accepted = (
        db.scalar(
            select(func.count()).where(
                Invoice.fecha_emision >= start,
                Invoice.fecha_emision < end,
                Invoice.estado_dgii == "ACEPTADO",
            )
        )
        or 0
    )
    invoices_rejected = (
        db.scalar(
            select(func.count()).where(
                Invoice.fecha_emision >= start,
                Invoice.fecha_emision < end,
                Invoice.estado_dgii == "RECHAZADO",
            )
        )
        or 0
    )
    invoices_other = max(int(invoices_month) - int(invoices_accepted) - int(invoices_rejected), 0)

    amount_due_month = (
        db.scalar(
            select(func.coalesce(func.sum(UsageRecord.monto_cargado), 0)).where(
                UsageRecord.fecha >= start,
                UsageRecord.fecha < end,
            )
        )
        or Decimal("0")
    )

    return DashboardKpisResponse(
        month=month,
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        companies_active=int(companies_active),
        invoices_month=int(invoices_month),
        invoices_accepted=int(invoices_accepted),
        invoices_rejected=int(invoices_rejected),
        invoices_other=int(invoices_other),
        amount_due_month=Decimal(str(amount_due_month)),
    )


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tenant_id: int | None = Query(default=None, ge=1),
    estado_dgii: str | None = Query(default=None, max_length=30),
    tipo_ecf: str | None = Query(default=None, max_length=3),
    encf: str | None = Query(default=None, max_length=20),
    track_id: str | None = Query(default=None, max_length=64),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> InvoiceListResponse:
    base = select(Invoice, Tenant.name).join(Tenant, Tenant.id == Invoice.tenant_id)
    if tenant_id is not None:
        base = base.where(Invoice.tenant_id == tenant_id)
    if estado_dgii:
        base = base.where(Invoice.estado_dgii == estado_dgii)
    if tipo_ecf:
        base = base.where(Invoice.tipo_ecf == tipo_ecf)
    if encf:
        base = base.where(Invoice.encf == encf)
    if track_id:
        base = base.where(Invoice.track_id == track_id)
    if date_from is not None:
        base = base.where(Invoice.fecha_emision >= date_from)
    if date_to is not None:
        base = base.where(Invoice.fecha_emision < date_to)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    stmt = (
        base.order_by(Invoice.fecha_emision.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = db.execute(stmt).all()

    items: list[InvoiceListItem] = []
    for invoice, tenant_name in rows:
        items.append(
            InvoiceListItem(
                id=invoice.id,
                tenant_id=invoice.tenant_id,
                tenant_name=str(tenant_name),
                encf=invoice.encf,
                tipo_ecf=invoice.tipo_ecf,
                estado_dgii=invoice.estado_dgii,
                track_id=invoice.track_id,
                total=Decimal(str(invoice.total)),
                fecha_emision=invoice.fecha_emision,
            )
        )

    return InvoiceListResponse(items=items, total=int(total), page=page, size=size)


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceDetailResponse:
    row = db.execute(
        select(Invoice, Tenant.name)
        .join(Tenant, Tenant.id == Invoice.tenant_id)
        .where(Invoice.id == invoice_id)
        .limit(1)
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")
    invoice, tenant_name = row
    return InvoiceDetailResponse(
        id=invoice.id,
        tenant_id=invoice.tenant_id,
        tenant_name=str(tenant_name),
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


@router.get("/tenants/{tenant_id}", response_model=TenantItem)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)) -> TenantItem:
    tenant = _get_tenant_or_404(db, tenant_id)
    return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")


@router.put("/tenants/{tenant_id}", response_model=TenantItem)
def update_tenant(
    request: Request,
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
) -> TenantItem:
    platform_payload = _platform_payload(request)
    tenant = _get_tenant_or_404(db, tenant_id)

    updates = payload.model_dump(exclude_none=True)
    if "rnc" in updates and updates["rnc"] != tenant.rnc:
        existing = db.scalar(select(Tenant).where(Tenant.rnc == updates["rnc"], Tenant.id != tenant.id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RNC ya registrado")

    for field, value in updates.items():
        setattr(tenant, field, value)

    db.flush()
    _append_audit_log(
        db,
        tenant_id=tenant.id,
        payload=platform_payload,
        action="TENANT_UPDATED",
        resource=f"tenant:{tenant.id}",
    )

    return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")


@router.get("/plans", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)) -> List[PlanResponse]:
    plans = db.scalars(select(Plan).order_by(Plan.name)).all()
    return [PlanResponse.model_validate(plan, from_attributes=True) for plan in plans]


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    request: Request,
    payload: PlanCreate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    platform_payload = _platform_payload(request)
    plan = Plan(**payload.model_dump())
    db.add(plan)
    db.flush()
    tenant_id = int(platform_payload.get("tenant_id") or 0)
    if tenant_id:
        _append_audit_log(
            db,
            tenant_id=tenant_id,
            payload=platform_payload,
            action="PLAN_CREATED",
            resource=f"plan:{plan.id}",
        )
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    request: Request,
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    platform_payload = _platform_payload(request)
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(plan, field, value)
    db.flush()
    tenant_id = int(platform_payload.get("tenant_id") or 0)
    if tenant_id:
        _append_audit_log(
            db,
            tenant_id=tenant_id,
            payload=platform_payload,
            action="PLAN_UPDATED",
            resource=f"plan:{plan.id}",
        )
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    request: Request,
    plan_id: int,
    db: Session = Depends(get_db),
) -> Response:
    platform_payload = _platform_payload(request)
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    tenant_id = int(platform_payload.get("tenant_id") or 0)
    if tenant_id:
        _append_audit_log(
            db,
            tenant_id=tenant_id,
            payload=platform_payload,
            action="PLAN_DELETED",
            resource=f"plan:{plan.id}",
        )
    db.delete(plan)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tenants/{tenant_id}/accounting/summary", response_model=LedgerSummaryResponse)
def get_accounting_summary(tenant_id: int, db: Session = Depends(get_db)) -> LedgerSummaryResponse:
    _get_tenant_or_404(db, tenant_id)

    total_emitidos = db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id)) or 0
    total_aceptados = db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "ACEPTADO")) or 0
    total_rechazados = db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "RECHAZADO")) or 0
    total_monto = db.scalar(select(func.coalesce(func.sum(Invoice.total), 0)).where(Invoice.tenant_id == tenant_id)) or Decimal("0")

    contabilizados = db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.contabilizado.is_(True))) or 0

    series_data: dict[str, dict[str, Decimal | int]] = defaultdict(lambda: {"monto": Decimal("0"), "cantidad": 0})
    rows = db.execute(select(Invoice.fecha_emision, Invoice.total).where(Invoice.tenant_id == tenant_id)).all()
    for fecha_emision, total in rows:
        if not fecha_emision:
            continue
        periodo = fecha_emision.strftime("%Y-%m")
        bucket = series_data[periodo]
        bucket["cantidad"] = int(bucket["cantidad"]) + 1
        bucket["monto"] = bucket["monto"] + Decimal(str(total))

    series = [
        LedgerMonthlyStat(periodo=periodo, cantidad=bucket["cantidad"], monto=bucket["monto"])
        for periodo, bucket in sorted(series_data.items())
    ]

    return LedgerSummaryResponse(
        totales=LedgerTotals(
            total_emitidos=total_emitidos,
            total_aceptados=total_aceptados,
            total_rechazados=total_rechazados,
            total_monto=Decimal(str(total_monto)),
        ),
        contabilidad=LedgerStatusBreakdown(
            contabilizados=contabilizados,
            pendientes=max(total_emitidos - contabilizados, 0),
        ),
        series=series,
    )


@router.get("/tenants/{tenant_id}/accounting/ledger", response_model=LedgerPaginatedResponse)
def list_ledger_entries(
    tenant_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contabilizado: Optional[bool] = Query(None),
) -> LedgerPaginatedResponse:
    _get_tenant_or_404(db, tenant_id)

    base_query = (
        select(InvoiceLedgerEntry, Invoice)
        .join(Invoice, InvoiceLedgerEntry.invoice_id == Invoice.id, isouter=True)
        .where(InvoiceLedgerEntry.tenant_id == tenant_id)
    )

    if contabilizado is not None:
        base_query = base_query.where(Invoice.contabilizado.is_(contabilizado))

    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    stmt = (
        base_query.order_by(InvoiceLedgerEntry.fecha.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    entries = db.execute(stmt).all()

    items: list[LedgerEntryItem] = []
    for entry, invoice in entries:
        items.append(
            LedgerEntryItem(
                id=entry.id,
                invoice_id=entry.invoice_id,
                encf=invoice.encf if invoice else None,
                referencia=entry.referencia,
                cuenta=entry.cuenta,
                descripcion=entry.descripcion,
                debit=Decimal(str(entry.debit)),
                credit=Decimal(str(entry.credit)),
                fecha=entry.fecha,
            )
        )

    return LedgerPaginatedResponse(items=items, total=total, page=page, size=size)


@router.post("/tenants/{tenant_id}/accounting/ledger", response_model=LedgerEntryItem, status_code=status.HTTP_201_CREATED)
def create_ledger_entry(
    tenant_id: int,
    payload: LedgerEntryCreate,
    db: Session = Depends(get_db),
) -> LedgerEntryItem:
    _get_tenant_or_404(db, tenant_id)

    invoice: Optional[Invoice] = None
    if payload.invoice_id is not None:
        invoice = db.get(Invoice, payload.invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")

    entry = InvoiceLedgerEntry(
        tenant_id=tenant_id,
        invoice_id=payload.invoice_id,
        referencia=payload.referencia,
        cuenta=payload.cuenta,
        descripcion=payload.descripcion,
        debit=payload.debit,
        credit=payload.credit,
        fecha=payload.fecha,
    )
    db.add(entry)

    if invoice:
        invoice.contabilizado = True
        invoice.accounted_at = payload.fecha
        invoice.asiento_referencia = payload.referencia

    db.flush()

    return LedgerEntryItem(
        id=entry.id,
        invoice_id=entry.invoice_id,
        encf=invoice.encf if invoice else None,
        referencia=entry.referencia,
        cuenta=entry.cuenta,
        descripcion=entry.descripcion,
        debit=Decimal(str(entry.debit)),
        credit=Decimal(str(entry.credit)),
        fecha=entry.fecha,
    )


@router.get("/tenants/{tenant_id}/settings", response_model=TenantSettingsResponse)
def get_tenant_settings(tenant_id: int, db: Session = Depends(get_db)) -> TenantSettingsResponse:
    _get_tenant_or_404(db, tenant_id)
    settings = _get_settings(db, tenant_id)
    return TenantSettingsResponse(
        moneda=settings.moneda,
        cuenta_ingresos=settings.cuenta_ingresos,
        cuenta_itbis=settings.cuenta_itbis,
        cuenta_retenciones=settings.cuenta_retenciones,
        dias_credito=settings.dias_credito,
        correo_facturacion=settings.correo_facturacion,
        telefono_contacto=settings.telefono_contacto,
        notas=settings.notas,
        updated_at=settings.updated_at,
    )


@router.put("/tenants/{tenant_id}/plan", response_model=TenantPlanResponse)
def assign_tenant_plan(
    request: Request,
    tenant_id: int,
    payload: TenantPlanAssignment,
    db: Session = Depends(get_db),
) -> TenantPlanResponse:
    platform_payload = _platform_payload(request)
    tenant = _get_tenant_or_404(db, tenant_id)
    plan: Plan | None = None
    if payload.plan_id is not None:
        plan = db.get(Plan, payload.plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
        tenant.plan = plan
        tenant.pending_plan_id = None
        tenant.plan_change_requested_at = None
        tenant.plan_change_effective_at = None
    else:
        tenant.plan = None
        tenant.plan_id = None
        tenant.pending_plan_id = None
        tenant.plan_change_requested_at = None
        tenant.plan_change_effective_at = None
    db.flush()
    _append_audit_log(
        db,
        tenant_id=tenant.id,
        payload=platform_payload,
        action="TENANT_PLAN_ASSIGNED" if plan else "TENANT_PLAN_UNASSIGNED",
        resource=f"tenant:{tenant.id}:plan:{plan.id if plan else 'none'}",
    )
    response_plan = PlanResponse.model_validate(plan, from_attributes=True) if plan else None
    return TenantPlanResponse(tenant_id=tenant.id, plan=response_plan)


@router.get("/tenants/{tenant_id}/plan", response_model=TenantPlanResponse)
def get_tenant_plan(tenant_id: int, db: Session = Depends(get_db)) -> TenantPlanResponse:
    tenant = _get_tenant_or_404(db, tenant_id)
    plan = tenant.plan
    response_plan = PlanResponse.model_validate(plan, from_attributes=True) if plan else None
    return TenantPlanResponse(tenant_id=tenant.id, plan=response_plan)


@router.get("/billing/summary", response_model=BillingSummaryResponse)
def admin_billing_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> BillingSummaryResponse:
    if month:
        try:
            period = datetime.strptime(month, "%Y-%m")
        except ValueError as exc:  # pragma: no cover - validado por regex
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de mes inválido") from exc
    else:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        period = datetime(now.year, now.month, 1)
        month = period.strftime("%Y-%m")

    rows = billing_summary(db, period)
    total_amount = sum((row["total_amount_due"] for row in rows), Decimal("0"))
    items = [BillingSummaryItem(**row) for row in rows]
    return BillingSummaryResponse(
        month=month,
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        items=items,
        total_amount_due=total_amount,
    )


@router.get("/audit-logs", response_model=List[AuditLogItem])
def list_audit_logs(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: int | None = Query(default=None, ge=1),
) -> List[AuditLogItem]:
    stmt = select(AuditLog)
    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    logs = db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [AuditLogItem.model_validate(log, from_attributes=True) for log in logs]


@router.get("/users", response_model=List[PlatformUserItem])
def list_platform_users(db: Session = Depends(get_db)) -> List[PlatformUserItem]:
    users = db.scalars(select(User).where(User.role.like("platform_%")).order_by(User.email.asc())).all()
    return [PlatformUserItem(id=user.id, email=user.email, role=user.role, scope="PLATFORM") for user in users]


@router.put("/tenants/{tenant_id}/settings", response_model=TenantSettingsResponse)
def update_tenant_settings(
    tenant_id: int,
    payload: TenantSettingsPayload,
    db: Session = Depends(get_db),
) -> TenantSettingsResponse:
    _get_tenant_or_404(db, tenant_id)
    settings = _get_settings(db, tenant_id)

    for field, value in payload.model_dump().items():
        setattr(settings, field, value)

    db.flush()

    return TenantSettingsResponse(
        moneda=settings.moneda,
        cuenta_ingresos=settings.cuenta_ingresos,
        cuenta_itbis=settings.cuenta_itbis,
        cuenta_retenciones=settings.cuenta_retenciones,
        dias_credito=settings.dias_credito,
        correo_facturacion=settings.correo_facturacion,
        telefono_contacto=settings.telefono_contacto,
        notas=settings.notas,
        updated_at=settings.updated_at,
    )
