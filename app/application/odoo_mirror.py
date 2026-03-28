"""Servicio de sincronizacion bidireccional limitada desde Odoo hacia EasyCounting."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.settings import settings as app_settings
from app.infrastructure.odoo.json2_client import OdooJSON2Client
from app.models.accounting import TenantSettings
from app.models.odoo_mirror import OdooInvoiceMirror, OdooPartnerMirror, OdooProductMirror


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


class OdooMirrorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def sync(
        self,
        *,
        tenant_id: int,
        include_customers: bool = True,
        include_vendors: bool = True,
        include_products: bool = True,
        include_invoices: bool = True,
        limit: int = 100,
    ) -> dict[str, int]:
        settings = self._resolve_settings(tenant_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        counts = {"customers": 0, "vendors": 0, "products": 0, "invoices": 0}

        async with OdooJSON2Client(
            base_url=settings["base_url"],
            api_key=settings["api_key"],
            database=settings["database"],
            timeout=app_settings.odoo_timeout_seconds,
        ) as client:
            if include_customers:
                rows = await client.search_read(
                    "res.partner",
                    domain=[["customer_rank", ">", 0]],
                    fields=["id", "name", "vat", "email", "phone", "company_type", "customer_rank", "supplier_rank"],
                    limit=limit,
                )
                counts["customers"] = self._upsert_partners(tenant_id=tenant_id, rows=rows, partner_kind="customer", synced_at=now)

            if include_vendors:
                rows = await client.search_read(
                    "res.partner",
                    domain=[["supplier_rank", ">", 0]],
                    fields=["id", "name", "vat", "email", "phone", "company_type", "customer_rank", "supplier_rank"],
                    limit=limit,
                )
                counts["vendors"] = self._upsert_partners(tenant_id=tenant_id, rows=rows, partner_kind="vendor", synced_at=now)

            if include_products:
                rows = await client.search_read(
                    "product.product",
                    domain=[],
                    fields=["id", "name", "default_code", "list_price", "standard_price", "active"],
                    limit=limit,
                )
                counts["products"] = self._upsert_products(tenant_id=tenant_id, rows=rows, synced_at=now)

            if include_invoices:
                rows = await client.search_read(
                    "account.move",
                    domain=[["move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]]],
                    fields=[
                        "id",
                        "name",
                        "move_type",
                        "state",
                        "payment_state",
                        "invoice_date",
                        "amount_total",
                        "amount_tax",
                        "amount_untaxed",
                        "partner_id",
                        "partner_name",
                        "partner_vat",
                        "ref",
                        "invoice_line_ids",
                    ],
                    limit=limit,
                )
                counts["invoices"] = self._upsert_invoices(tenant_id=tenant_id, rows=rows, synced_at=now)

        self.db.flush()
        return counts

    def list_partners(self, *, tenant_id: int, partner_kind: str, limit: int = 100) -> list[OdooPartnerMirror]:
        stmt = (
            select(OdooPartnerMirror)
            .where(OdooPartnerMirror.tenant_id == tenant_id, OdooPartnerMirror.partner_kind == partner_kind)
            .order_by(OdooPartnerMirror.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_products(self, *, tenant_id: int, limit: int = 100) -> list[OdooProductMirror]:
        stmt = (
            select(OdooProductMirror)
            .where(OdooProductMirror.tenant_id == tenant_id)
            .order_by(OdooProductMirror.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_invoices(self, *, tenant_id: int, limit: int = 100) -> list[OdooInvoiceMirror]:
        stmt = (
            select(OdooInvoiceMirror)
            .where(OdooInvoiceMirror.tenant_id == tenant_id)
            .order_by(OdooInvoiceMirror.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def _resolve_settings(self, tenant_id: int) -> dict[str, str]:
        tenant_settings = self.db.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
        base_url = (tenant_settings.odoo_api_url if tenant_settings else None) or app_settings.odoo_json2_base_url
        database = (tenant_settings.odoo_database if tenant_settings else None) or app_settings.odoo_json2_database
        api_key = app_settings.odoo_json2_api_key
        if not base_url or not database or not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuracion Odoo incompleta para sincronizacion (base_url, database o api_key).",
            )
        if not ((tenant_settings and tenant_settings.odoo_sync_enabled) or app_settings.odoo_sync_enabled):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sincronizacion Odoo deshabilitada para este tenant.",
            )
        return {"base_url": base_url, "database": database, "api_key": api_key}

    def _upsert_partners(
        self,
        *,
        tenant_id: int,
        rows: list[dict[str, Any]],
        partner_kind: str,
        synced_at: datetime,
    ) -> int:
        affected = 0
        for row in rows:
            odoo_id = int(row["id"])
            existing = self.db.scalar(
                select(OdooPartnerMirror).where(
                    OdooPartnerMirror.tenant_id == tenant_id,
                    OdooPartnerMirror.odoo_id == odoo_id,
                    OdooPartnerMirror.partner_kind == partner_kind,
                )
            )
            if existing is None:
                existing = OdooPartnerMirror(tenant_id=tenant_id, odoo_id=odoo_id, partner_kind=partner_kind, name=str(row.get("name") or ""))
                self.db.add(existing)
            existing.name = str(row.get("name") or existing.name)
            existing.vat = row.get("vat")
            existing.email = row.get("email")
            existing.phone = row.get("phone")
            existing.company_type = row.get("company_type")
            existing.raw_json = row
            existing.synced_at = synced_at
            affected += 1
        return affected

    def _upsert_products(self, *, tenant_id: int, rows: list[dict[str, Any]], synced_at: datetime) -> int:
        affected = 0
        for row in rows:
            odoo_id = int(row["id"])
            existing = self.db.scalar(
                select(OdooProductMirror).where(OdooProductMirror.tenant_id == tenant_id, OdooProductMirror.odoo_id == odoo_id)
            )
            if existing is None:
                existing = OdooProductMirror(tenant_id=tenant_id, odoo_id=odoo_id, name=str(row.get("name") or ""))
                self.db.add(existing)
            existing.name = str(row.get("name") or existing.name)
            existing.default_code = row.get("default_code")
            existing.list_price = _to_decimal(row.get("list_price"))
            existing.standard_price = _to_decimal(row.get("standard_price"))
            existing.active = bool(row.get("active", True))
            existing.raw_json = row
            existing.synced_at = synced_at
            affected += 1
        return affected

    def _upsert_invoices(self, *, tenant_id: int, rows: list[dict[str, Any]], synced_at: datetime) -> int:
        affected = 0
        for row in rows:
            odoo_id = int(row["id"])
            existing = self.db.scalar(
                select(OdooInvoiceMirror).where(OdooInvoiceMirror.tenant_id == tenant_id, OdooInvoiceMirror.odoo_id == odoo_id)
            )
            if existing is None:
                existing = OdooInvoiceMirror(tenant_id=tenant_id, odoo_id=odoo_id)
                self.db.add(existing)
            existing.move_name = row.get("name")
            existing.move_type = row.get("move_type")
            existing.state = row.get("state")
            existing.payment_state = row.get("payment_state")
            invoice_date = row.get("invoice_date")
            if isinstance(invoice_date, str) and invoice_date:
                try:
                    existing.invoice_date = datetime.fromisoformat(invoice_date)
                except ValueError:
                    existing.invoice_date = None
            existing.partner_name = row.get("partner_name")
            existing.partner_vat = row.get("partner_vat")
            existing.amount_total = _to_decimal(row.get("amount_total"))
            existing.amount_tax = _to_decimal(row.get("amount_tax"))
            existing.amount_untaxed = _to_decimal(row.get("amount_untaxed"))
            existing.encf = row.get("ref") if isinstance(row.get("ref"), str) else None
            existing.raw_json = row
            existing.lines_json = {"invoice_line_ids": row.get("invoice_line_ids") or []}
            existing.synced_at = synced_at
            affected += 1
        return affected
