"""Application services for admin portal operations."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from typing import List, Optional

from fastapi import HTTPException, status
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
    PlatformAIProviderItem,
    PlatformAIProviderPayload,
    PlatformUserItem,
)
from app.infra.settings import settings as app_settings
from app.models.billing import Plan, UsageRecord
from app.models.accounting import InvoiceLedgerEntry, TenantSettings
from app.models.audit import AuditLog
from app.models.invoice import Invoice
from app.models.platform_ai import PlatformAIProvider
from app.models.tenant import Tenant
from app.models.user import User
from app.portal_admin.reports import billing_summary
from app.services.platform_ai import (
    SUPPORTED_AI_PROVIDER_TYPES,
    decrypt_secret,
    dumps_extra_headers,
    encrypt_secret,
    ensure_platform_ai_table,
    mask_secret,
    normalize_base_url,
    parse_extra_headers,
)


def _month_range(month: datetime) -> tuple[datetime, datetime]:
    start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


class AdminService:
    def __init__(self, db: Session, platform_payload: dict | None = None) -> None:
        self.db = db
        self.platform_payload = platform_payload or {}

    def _get_tenant_or_404(self, tenant_id: int) -> Tenant:
        tenant = self.db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        return tenant

    def _get_settings(self, tenant_id: int) -> TenantSettings:
        tenant_settings = self.db.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
        if tenant_settings:
            return tenant_settings
        tenant_settings = TenantSettings(tenant_id=tenant_id)
        self.db.add(tenant_settings)
        self.db.flush()
        return tenant_settings

    def _require_platform_superroot(self) -> None:
        role = self.platform_payload.get("role")
        if role != "platform_superroot":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta configuracion solo esta disponible para superroot",
            )

    def _platform_actor_tenant_id(self) -> int | None:
        tenant_id = self.platform_payload.get("tenant_id")
        try:
            tenant_pk = int(tenant_id) if tenant_id is not None else None
        except (TypeError, ValueError):
            tenant_pk = None
        if tenant_pk is None:
            return None
        tenant = self.db.get(Tenant, tenant_pk)
        return tenant.id if tenant else None

    def _append_platform_audit_log(self, *, action: str, resource: str) -> None:
        tenant_id = self._platform_actor_tenant_id()
        if tenant_id is None:
            return
        self._append_audit_log(tenant_id=tenant_id, action=action, resource=resource)

    def _to_platform_ai_provider_item(self, provider: PlatformAIProvider) -> PlatformAIProviderItem:
        raw_api_key = decrypt_secret(provider.encrypted_api_key)
        return PlatformAIProviderItem(
            id=provider.id,
            display_name=provider.display_name,
            provider_type=provider.provider_type,
            enabled=bool(provider.enabled),
            is_default=bool(provider.is_default),
            base_url=normalize_base_url(provider.provider_type, provider.base_url),
            model=provider.model,
            api_key_configured=bool(raw_api_key),
            api_key_masked=mask_secret(raw_api_key),
            organization_id=provider.organization_id,
            project_id=provider.project_id,
            api_version=provider.api_version,
            system_prompt=provider.system_prompt,
            extra_headers=parse_extra_headers(provider.extra_headers_json),
            timeout_seconds=float(provider.timeout_seconds),
            max_completion_tokens=int(provider.max_completion_tokens),
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    def _actor_from_payload(self, payload: dict) -> str:
        subject = payload.get("sub")
        role = payload.get("role")
        try:
            user_id = int(subject) if subject is not None else None
        except (TypeError, ValueError):
            user_id = None
        if user_id is not None:
            user = self.db.get(User, user_id)
            if user:
                return user.email
        if isinstance(subject, str) and subject:
            if isinstance(role, str) and role:
                return f"user:{subject}:{role}"
            return f"user:{subject}"
        return "unknown"

    def _append_audit_log(self, *, tenant_id: int, action: str, resource: str) -> None:
        last = self.db.scalar(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.id.desc())
            .limit(1)
        )
        hash_prev = last.hash_curr if last else "0" * 64
        actor = self._actor_from_payload(self.platform_payload)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        raw = f"{tenant_id}|{actor}|{action}|{resource}|{hash_prev}|{now.isoformat()}"
        hash_curr = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.db.add(
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

    def list_tenants(self) -> List[TenantItem]:
        tenants = self.db.scalars(select(Tenant).order_by(Tenant.id.desc())).all()
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

    def create_tenant(self, payload: TenantCreate) -> TenantItem:
        existing = self.db.scalar(select(Tenant).where(Tenant.rnc == payload.rnc))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RNC ya registrado")

        default_plan = self.db.scalar(select(Plan).where(Plan.name == "Emprendedor").limit(1))

        tenant = Tenant(
            name=payload.name,
            rnc=payload.rnc,
            env=payload.env,
            plan_id=default_plan.id if default_plan else None,
            dgii_base_ecf=str(payload.dgii_base_ecf or app_settings.dgii_recepcion_base_url),
            dgii_base_fc=str(payload.dgii_base_fc or app_settings.dgii_recepcion_fc_base_url),
        )
        self.db.add(tenant)
        self.db.flush()
        self._append_audit_log(
            tenant_id=tenant.id,
            action="TENANT_CREATED",
            resource=f"tenant:{tenant.id}",
        )
        return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")

    def update_tenant(self, tenant_id: int, payload: TenantUpdate) -> TenantItem:
        tenant = self._get_tenant_or_404(tenant_id)

        updates = payload.model_dump(exclude_none=True)
        if "rnc" in updates and updates["rnc"] != tenant.rnc:
            existing = self.db.scalar(select(Tenant).where(Tenant.rnc == updates["rnc"], Tenant.id != tenant.id))
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="RNC ya registrado")

        for field, value in updates.items():
            setattr(tenant, field, value)

        self.db.flush()
        self._append_audit_log(
            tenant_id=tenant.id,
            action="TENANT_UPDATED",
            resource=f"tenant:{tenant.id}",
        )

        return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")

    def get_tenant(self, tenant_id: int) -> TenantItem:
        tenant = self._get_tenant_or_404(tenant_id)
        return TenantItem(id=tenant.id, name=tenant.name, rnc=tenant.rnc, env=tenant.env, status="Activa")

    def dashboard_kpis(self, month: str | None) -> DashboardKpisResponse:
        if month:
            try:
                period = datetime.strptime(month, "%Y-%m")
            except ValueError as exc:  # pragma: no cover
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de mes inválido") from exc
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            period = datetime(now.year, now.month, 1)
            month = period.strftime("%Y-%m")

        start, end = _month_range(period)

        companies_active = self.db.scalar(select(func.count()).select_from(Tenant)) or 0
        invoices_month = (
            self.db.scalar(
                select(func.count()).where(
                    Invoice.fecha_emision >= start,
                    Invoice.fecha_emision < end,
                )
            )
            or 0
        )
        invoices_accepted = (
            self.db.scalar(
                select(func.count()).where(
                    Invoice.fecha_emision >= start,
                    Invoice.fecha_emision < end,
                    Invoice.estado_dgii == "ACEPTADO",
                )
            )
            or 0
        )
        invoices_rejected = (
            self.db.scalar(
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
            self.db.scalar(
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

    def list_invoices(
        self,
        *,
        page: int,
        size: int,
        tenant_id: int | None,
        estado_dgii: str | None,
        tipo_ecf: str | None,
        encf: str | None,
        track_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
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

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        stmt = (
            base.order_by(Invoice.fecha_emision.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = self.db.execute(stmt).all()

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

    def get_invoice(self, invoice_id: int) -> InvoiceDetailResponse:
        row = self.db.execute(
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

    def list_plans(self) -> List[PlanResponse]:
        plans = self.db.scalars(select(Plan).order_by(Plan.name)).all()
        return [PlanResponse.model_validate(plan, from_attributes=True) for plan in plans]

    def create_plan(self, payload: PlanCreate) -> PlanResponse:
        plan = Plan(**payload.model_dump())
        self.db.add(plan)
        self.db.flush()
        tenant_id = int(self.platform_payload.get("tenant_id") or 0)
        if tenant_id:
            self._append_audit_log(
                tenant_id=tenant_id,
                action="PLAN_CREATED",
                resource=f"plan:{plan.id}",
            )
        return PlanResponse.model_validate(plan, from_attributes=True)

    def update_plan(self, plan_id: int, payload: PlanUpdate) -> PlanResponse:
        plan = self.db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(plan, field, value)
        self.db.flush()
        tenant_id = int(self.platform_payload.get("tenant_id") or 0)
        if tenant_id:
            self._append_audit_log(
                tenant_id=tenant_id,
                action="PLAN_UPDATED",
                resource=f"plan:{plan.id}",
            )
        return PlanResponse.model_validate(plan, from_attributes=True)

    def delete_plan(self, plan_id: int) -> None:
        plan = self.db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
        tenant_id = int(self.platform_payload.get("tenant_id") or 0)
        if tenant_id:
            self._append_audit_log(
                tenant_id=tenant_id,
                action="PLAN_DELETED",
                resource=f"plan:{plan.id}",
            )
        self.db.delete(plan)
        self.db.flush()

    def get_accounting_summary(self, tenant_id: int) -> LedgerSummaryResponse:
        self._get_tenant_or_404(tenant_id)

        total_emitidos = self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id)) or 0
        total_aceptados = self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "ACEPTADO")) or 0
        total_rechazados = self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "RECHAZADO")) or 0
        total_monto = self.db.scalar(select(func.coalesce(func.sum(Invoice.total), 0)).where(Invoice.tenant_id == tenant_id)) or Decimal("0")

        contabilizados = self.db.scalar(select(func.count()).where(Invoice.tenant_id == tenant_id, Invoice.contabilizado.is_(True))) or 0

        series_data: dict[str, dict[str, Decimal | int]] = defaultdict(lambda: {"monto": Decimal("0"), "cantidad": 0})
        rows = self.db.execute(select(Invoice.fecha_emision, Invoice.total).where(Invoice.tenant_id == tenant_id)).all()
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

    def list_ledger_entries(
        self,
        *,
        tenant_id: int,
        page: int,
        size: int,
        contabilizado: Optional[bool],
    ) -> LedgerPaginatedResponse:
        self._get_tenant_or_404(tenant_id)

        base_query = (
            select(InvoiceLedgerEntry, Invoice)
            .join(Invoice, InvoiceLedgerEntry.invoice_id == Invoice.id, isouter=True)
            .where(InvoiceLedgerEntry.tenant_id == tenant_id)
        )

        if contabilizado is not None:
            base_query = base_query.where(Invoice.contabilizado.is_(contabilizado))

        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        stmt = (
            base_query.order_by(InvoiceLedgerEntry.fecha.desc())
            .offset((page - 1) * size)
            .limit(size)
        )

        entries = self.db.execute(stmt).all()

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

    def create_ledger_entry(self, tenant_id: int, payload: LedgerEntryCreate) -> LedgerEntryItem:
        self._get_tenant_or_404(tenant_id)

        invoice: Optional[Invoice] = None
        if payload.invoice_id is not None:
            invoice = self.db.get(Invoice, payload.invoice_id)
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
        self.db.add(entry)

        if invoice:
            invoice.contabilizado = True
            invoice.accounted_at = payload.fecha
            invoice.asiento_referencia = payload.referencia

        self.db.flush()

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

    def get_tenant_settings(self, tenant_id: int) -> TenantSettingsResponse:
        self._get_tenant_or_404(tenant_id)
        settings = self._get_settings(tenant_id)
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

    def update_tenant_settings(self, tenant_id: int, payload: TenantSettingsPayload) -> TenantSettingsResponse:
        self._get_tenant_or_404(tenant_id)
        settings = self._get_settings(tenant_id)

        for field, value in payload.model_dump().items():
            setattr(settings, field, value)

        self.db.flush()

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

    def assign_tenant_plan(self, tenant_id: int, payload: TenantPlanAssignment) -> TenantPlanResponse:
        tenant = self._get_tenant_or_404(tenant_id)
        plan: Plan | None = None
        if payload.plan_id is not None:
            plan = self.db.get(Plan, payload.plan_id)
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
        self.db.flush()
        self._append_audit_log(
            tenant_id=tenant.id,
            action="TENANT_PLAN_ASSIGNED" if plan else "TENANT_PLAN_UNASSIGNED",
            resource=f"tenant:{tenant.id}:plan:{plan.id if plan else 'none'}",
        )
        response_plan = PlanResponse.model_validate(plan, from_attributes=True) if plan else None
        return TenantPlanResponse(tenant_id=tenant.id, plan=response_plan)

    def get_tenant_plan(self, tenant_id: int) -> TenantPlanResponse:
        tenant = self._get_tenant_or_404(tenant_id)
        plan = tenant.plan
        response_plan = PlanResponse.model_validate(plan, from_attributes=True) if plan else None
        return TenantPlanResponse(tenant_id=tenant.id, plan=response_plan)

    def admin_billing_summary(self, month: str | None) -> BillingSummaryResponse:
        if month:
            try:
                period = datetime.strptime(month, "%Y-%m")
            except ValueError as exc:  # pragma: no cover
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de mes inválido") from exc
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            period = datetime(now.year, now.month, 1)
            month = period.strftime("%Y-%m")

        rows = billing_summary(self.db, period)
        total_amount = sum((row["total_amount_due"] for row in rows), Decimal("0"))
        items = [BillingSummaryItem(**row) for row in rows]
        return BillingSummaryResponse(
            month=month,
            generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            items=items,
            total_amount_due=total_amount,
        )

    def list_audit_logs(self, limit: int, tenant_id: int | None) -> List[AuditLogItem]:
        stmt = select(AuditLog)
        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        logs = self.db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(limit)).all()
        return [AuditLogItem.model_validate(log, from_attributes=True) for log in logs]

    def list_platform_users(self) -> List[PlatformUserItem]:
        users = self.db.scalars(select(User).where(User.role.like("platform_%")).order_by(User.email.asc())).all()
        return [PlatformUserItem(id=user.id, email=user.email, role=user.role, scope="PLATFORM") for user in users]

    def list_platform_ai_providers(self) -> List[PlatformAIProviderItem]:
        self._require_platform_superroot()
        ensure_platform_ai_table(self.db)
        providers = self.db.scalars(
            select(PlatformAIProvider).order_by(PlatformAIProvider.is_default.desc(), PlatformAIProvider.display_name.asc())
        ).all()
        return [self._to_platform_ai_provider_item(provider) for provider in providers]

    def create_platform_ai_provider(self, payload: PlatformAIProviderPayload) -> PlatformAIProviderItem:
        self._require_platform_superroot()
        ensure_platform_ai_table(self.db)
        if payload.provider_type not in SUPPORTED_AI_PROVIDER_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proveedor IA no soportado")
        if payload.is_default and not payload.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El proveedor por defecto debe estar habilitado")

        if payload.is_default:
            for current in self.db.scalars(select(PlatformAIProvider).where(PlatformAIProvider.is_default.is_(True))).all():
                current.is_default = False

        provider = PlatformAIProvider(
            display_name=payload.display_name,
            provider_type=payload.provider_type,
            enabled=payload.enabled,
            is_default=payload.is_default,
            base_url=(payload.base_url or "").strip() or None,
            model=payload.model,
            encrypted_api_key=encrypt_secret(payload.api_key),
            organization_id=payload.organization_id,
            project_id=payload.project_id,
            api_version=payload.api_version,
            system_prompt=payload.system_prompt,
            extra_headers_json=dumps_extra_headers(payload.extra_headers),
            timeout_seconds=payload.timeout_seconds,
            max_completion_tokens=payload.max_completion_tokens,
        )
        self.db.add(provider)
        self.db.flush()
        self._append_platform_audit_log(action="PLATFORM_AI_PROVIDER_CREATED", resource=f"platform_ai_provider:{provider.id}")
        return self._to_platform_ai_provider_item(provider)

    def update_platform_ai_provider(self, provider_id: int, payload: PlatformAIProviderPayload) -> PlatformAIProviderItem:
        self._require_platform_superroot()
        ensure_platform_ai_table(self.db)
        if payload.provider_type not in SUPPORTED_AI_PROVIDER_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proveedor IA no soportado")
        if payload.is_default and not payload.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El proveedor por defecto debe estar habilitado")
        provider = self.db.get(PlatformAIProvider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor IA no encontrado")

        if payload.is_default:
            for current in self.db.scalars(
                select(PlatformAIProvider).where(
                    PlatformAIProvider.is_default.is_(True),
                    PlatformAIProvider.id != provider.id,
                )
            ).all():
                current.is_default = False

        provider.display_name = payload.display_name
        provider.provider_type = payload.provider_type
        provider.enabled = payload.enabled
        provider.is_default = payload.is_default
        provider.base_url = (payload.base_url or "").strip() or None
        provider.model = payload.model
        provider.organization_id = payload.organization_id
        provider.project_id = payload.project_id
        provider.api_version = payload.api_version
        provider.system_prompt = payload.system_prompt
        provider.extra_headers_json = dumps_extra_headers(payload.extra_headers)
        provider.timeout_seconds = payload.timeout_seconds
        provider.max_completion_tokens = payload.max_completion_tokens
        if payload.clear_api_key:
            provider.encrypted_api_key = None
        elif payload.api_key is not None and payload.api_key.strip():
            provider.encrypted_api_key = encrypt_secret(payload.api_key)

        self.db.flush()
        self._append_platform_audit_log(action="PLATFORM_AI_PROVIDER_UPDATED", resource=f"platform_ai_provider:{provider.id}")
        return self._to_platform_ai_provider_item(provider)

    def delete_platform_ai_provider(self, provider_id: int) -> None:
        self._require_platform_superroot()
        ensure_platform_ai_table(self.db)
        provider = self.db.get(PlatformAIProvider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proveedor IA no encontrado")
        self._append_platform_audit_log(action="PLATFORM_AI_PROVIDER_DELETED", resource=f"platform_ai_provider:{provider.id}")
        self.db.delete(provider)
        self.db.flush()
