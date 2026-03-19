from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Iterable
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.partner import PartnerAccount, PartnerTenantAssignment
from app.models.tenant import Tenant
from app.models.user import User
from app.partner.schemas import (
    PartnerDashboardResponse,
    PartnerEmitRequest,
    PartnerEmitResponse,
    PartnerInvoiceItem,
    PartnerInvoiceListResponse,
    PartnerProfile,
    PartnerTenantItem,
    PartnerTenantOverview,
)


class PartnerPortalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario partner no encontrado")
        if not user.role.startswith("partner_"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta no autorizada para portal seller")
        if user.partner_account_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta partner sin asociacion comercial")
        return user

    def _get_partner_account(self, user: User) -> PartnerAccount:
        account = self.db.get(PartnerAccount, user.partner_account_id)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta seller no encontrada")
        return account

    def _assignment_map(self, partner_account_id: int) -> dict[int, PartnerTenantAssignment]:
        assignments = self.db.scalars(
            select(PartnerTenantAssignment).where(PartnerTenantAssignment.partner_account_id == partner_account_id)
        ).all()
        return {assignment.tenant_id: assignment for assignment in assignments}

    def _tenant_items(self, assignments: Iterable[PartnerTenantAssignment]) -> list[PartnerTenantItem]:
        assignment_list = list(assignments)
        if not assignment_list:
            return []

        tenant_ids = [assignment.tenant_id for assignment in assignment_list]
        totals = {
            row.tenant_id: (
                int(row.invoice_count or 0),
                Decimal(str(row.total_amount or 0)),
            )
            for row in self.db.execute(
                select(
                    Invoice.tenant_id.label("tenant_id"),
                    func.count(Invoice.id).label("invoice_count"),
                    func.coalesce(func.sum(Invoice.total), 0).label("total_amount"),
                )
                .where(Invoice.tenant_id.in_(tenant_ids))
                .group_by(Invoice.tenant_id)
            ).all()
        }

        items: list[PartnerTenantItem] = []
        for assignment in assignment_list:
            tenant = assignment.tenant
            if tenant is None:
                continue
            invoice_count, total_amount = totals.get(tenant.id, (0, Decimal("0")))
            items.append(
                PartnerTenantItem(
                    id=tenant.id,
                    name=tenant.name,
                    rnc=tenant.rnc,
                    env=tenant.env,
                    status="Activa",
                    can_emit=bool(assignment.can_emit),
                    can_manage=bool(assignment.can_manage),
                    invoice_count=invoice_count,
                    total_amount=total_amount,
                )
            )
        return items

    def get_profile(self, user_id: int) -> PartnerProfile:
        user = self._get_user(user_id)
        account = self._get_partner_account(user)
        return PartnerProfile(
            account_id=account.id,
            account_name=account.name,
            account_slug=account.slug,
            user_email=user.email,
            role=user.role,
        )

    def dashboard(self, user_id: int) -> PartnerDashboardResponse:
        user = self._get_user(user_id)
        account = self._get_partner_account(user)
        assignments = self.db.scalars(
            select(PartnerTenantAssignment)
            .where(PartnerTenantAssignment.partner_account_id == account.id)
            .join(PartnerTenantAssignment.tenant)
            .order_by(Tenant.name.asc())
        ).all()
        items = self._tenant_items(assignments)
        tenant_ids = [item.id for item in items]
        invoice_rows = self.db.execute(
            select(
                Invoice.estado_dgii,
                func.count(Invoice.id),
                func.coalesce(func.sum(Invoice.total), 0),
            )
            .where(Invoice.tenant_id.in_(tenant_ids) if tenant_ids else False)
            .group_by(Invoice.estado_dgii)
        ).all()
        invoice_count = sum(int(count or 0) for _state, count, _amount in invoice_rows)
        accepted_count = sum(int(count or 0) for state, count, _amount in invoice_rows if state == "ACEPTADO")
        pending_count = sum(
            int(count or 0) for state, count, _amount in invoice_rows if state not in {"ACEPTADO", "RECHAZADO"}
        )
        total_amount = sum(Decimal(str(amount or 0)) for _state, _count, amount in invoice_rows)
        return PartnerDashboardResponse(
            partner=PartnerProfile(
                account_id=account.id,
                account_name=account.name,
                account_slug=account.slug,
                user_email=user.email,
                role=user.role,
            ),
            tenant_count=len(items),
            invoice_count=invoice_count,
            accepted_count=accepted_count,
            pending_count=pending_count,
            total_amount=total_amount,
            tenants=items,
        )

    def list_tenants(self, user_id: int) -> list[PartnerTenantItem]:
        user = self._get_user(user_id)
        account = self._get_partner_account(user)
        assignments = self.db.scalars(
            select(PartnerTenantAssignment)
            .where(PartnerTenantAssignment.partner_account_id == account.id)
            .join(PartnerTenantAssignment.tenant)
            .order_by(Tenant.name.asc())
        ).all()
        return self._tenant_items(assignments)

    def _get_assignment_or_403(self, *, user_id: int, tenant_id: int) -> PartnerTenantAssignment:
        user = self._get_user(user_id)
        assignment = self.db.scalar(
            select(PartnerTenantAssignment).where(
                PartnerTenantAssignment.partner_account_id == user.partner_account_id,
                PartnerTenantAssignment.tenant_id == tenant_id,
            )
        )
        if not assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant no asignado al reseller")
        return assignment

    def get_tenant_overview(self, *, user_id: int, tenant_id: int) -> PartnerTenantOverview:
        assignment = self._get_assignment_or_403(user_id=user_id, tenant_id=tenant_id)
        tenant_item = self._tenant_items([assignment])[0]
        accepted_count = self.db.scalar(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "ACEPTADO")
        ) or 0
        rejected_count = self.db.scalar(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id, Invoice.estado_dgii == "RECHAZADO")
        ) or 0
        last_invoice = self.db.scalar(
            select(Invoice).where(Invoice.tenant_id == tenant_id).order_by(Invoice.fecha_emision.desc()).limit(1)
        )
        return PartnerTenantOverview(
            tenant=tenant_item,
            accepted_count=int(accepted_count),
            rejected_count=int(rejected_count),
            last_encf=last_invoice.encf if last_invoice else None,
            last_track_id=last_invoice.track_id if last_invoice else None,
            last_invoice_at=last_invoice.fecha_emision if last_invoice else None,
        )

    def list_invoices(self, *, user_id: int, tenant_id: int | None, page: int, size: int) -> PartnerInvoiceListResponse:
        user = self._get_user(user_id)
        assignment_map = self._assignment_map(user.partner_account_id or 0)
        allowed_tenant_ids = list(assignment_map.keys())
        if not allowed_tenant_ids:
            return PartnerInvoiceListResponse(items=[], total=0, page=page, size=size)
        if tenant_id is not None and tenant_id not in assignment_map:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant no asignado al reseller")

        stmt = (
            select(Invoice, Tenant)
            .join(Tenant, Tenant.id == Invoice.tenant_id)
            .where(Invoice.tenant_id.in_(allowed_tenant_ids))
        )
        if tenant_id is not None:
            stmt = stmt.where(Invoice.tenant_id == tenant_id)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.execute(
            stmt.order_by(Invoice.fecha_emision.desc()).offset((page - 1) * size).limit(size)
        ).all()
        items = [
            PartnerInvoiceItem(
                id=invoice.id,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                encf=invoice.encf,
                tipo_ecf=invoice.tipo_ecf,
                estado_dgii=invoice.estado_dgii,
                track_id=invoice.track_id,
                total=Decimal(str(invoice.total)),
                fecha_emision=invoice.fecha_emision,
            )
            for invoice, tenant in rows
        ]
        return PartnerInvoiceListResponse(items=items, total=int(total), page=page, size=size)

    def emit_demo_invoice(self, *, user_id: int, payload: PartnerEmitRequest) -> PartnerEmitResponse:
        user = self._get_user(user_id)
        assignment = self._get_assignment_or_403(user_id=user.id, tenant_id=payload.tenant_id)
        if user.role == "partner_auditor" or not assignment.can_emit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta seller sin permisos de emision")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        track_id = f"partner-demo-{uuid4().hex[:12]}"
        xml_path = f"/var/getupsoft/storage/partner-demo/{payload.encf}.xml"
        xml_hash = sha256(f"{payload.encf}|{payload.tenant_id}|{payload.total}".encode("utf-8")).hexdigest()
        invoice = Invoice(
            tenant_id=payload.tenant_id,
            encf=payload.encf,
            tipo_ecf=payload.tipo_ecf,
            rnc_receptor=payload.rnc_receptor,
            xml_path=xml_path,
            xml_hash=xml_hash,
            estado_dgii="SIMULADO",
            track_id=track_id,
            codigo_seguridad=None,
            total=float(payload.total),
            fecha_emision=now,
        )
        self.db.add(invoice)
        self.db.flush()
        return PartnerEmitResponse(
            invoice_id=invoice.id,
            tenant_id=invoice.tenant_id,
            encf=invoice.encf,
            estado_dgii=invoice.estado_dgii,
            track_id=track_id,
            total=Decimal(str(invoice.total)),
            message="Comprobante seller generado en modo demo.",
        )
