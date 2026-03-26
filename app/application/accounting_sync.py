"""Odoo accounting synchronization over the durable fiscal operation core."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.application.fiscal_operations import FiscalOperationService
from app.infra.settings import settings as app_settings
from app.infrastructure.odoo.json2_client import OdooJSON2Client
from app.infrastructure.odoo.mappers import build_move_payload, build_partner_domain, build_partner_values
from app.infrastructure.odoo.reconciliation import normalize_move_snapshot, sync_state_from_snapshot
from app.models.accounting import TenantSettings
from app.models.fiscal_operation import FiscalOperation
from app.models.invoice import Invoice
from app.shared.time import utcnow


class AccountingSyncResult(dict):
    """Small typed dictionary for sync results."""


class OdooAccountingSyncService:
    """Synchronize invoices from FastAPI into Odoo 19 JSON-2."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.operations = FiscalOperationService(db)

    async def sync_operation(self, operation: FiscalOperation) -> AccountingSyncResult:
        invoice = operation.invoice
        if invoice is None:
            return AccountingSyncResult(status="SKIPPED", reason="invoice_missing")
        tenant_settings = self.db.query(TenantSettings).filter(TenantSettings.tenant_id == operation.tenant_id).one_or_none()
        if tenant_settings is None:
            self.operations.record_event(
                operation,
                status=operation.state,
                title="Sin parametros Odoo",
                message="No existe TenantSettings para sincronizacion",
                stage="SYNCING_TO_ODOO",
            )
            return AccountingSyncResult(status="SKIPPED", reason="tenant_settings_missing")
        if not tenant_settings.odoo_sync_enabled and not app_settings.odoo_sync_enabled:
            self.operations.record_event(
                operation,
                status=operation.state,
                title="Sincronizacion Odoo deshabilitada",
                message="No se intento sincronizar porque el tenant no la habilito",
                stage="SYNCING_TO_ODOO",
            )
            invoice.odoo_sync_state = "SKIPPED"
            self.db.flush()
            return AccountingSyncResult(status="SKIPPED", reason="disabled")

        base_url = tenant_settings.odoo_api_url or app_settings.odoo_json2_base_url
        database = tenant_settings.odoo_database or app_settings.odoo_json2_database
        api_key = app_settings.odoo_json2_api_key
        if not base_url or not database or not api_key:
            self.operations.record_event(
                operation,
                status=operation.state,
                title="Configuracion Odoo incompleta",
                message="Faltan base_url, database o api_key de Odoo",
                stage="SYNCING_TO_ODOO",
            )
            invoice.odoo_sync_state = "CONFIGURATION_MISSING"
            self.db.flush()
            return AccountingSyncResult(status="SKIPPED", reason="configuration_missing")

        self.operations.transition(
            operation,
            state="SYNCING_TO_ODOO",
            title="Sincronizando a Odoo",
            message="Preparando partner y account.move",
            details={"invoiceId": invoice.id, "encf": invoice.encf},
        )
        async with OdooJSON2Client(
            base_url=base_url,
            api_key=api_key,
            database=database,
            timeout=app_settings.odoo_timeout_seconds,
        ) as client:
            partner_domain = build_partner_domain(invoice)
            partner_values = build_partner_values(invoice, tenant_settings)
            attempt = self.operations.register_odoo_attempt(
                operation,
                remote_model="account.move",
                payload={"partner_domain": partner_domain, "partner_values": partner_values},
            )
            try:
                partner_id = await self._resolve_partner_id(client, partner_domain, partner_values)
                move_payload = build_move_payload(invoice, tenant_settings, partner_id=partner_id)
                attempt.payload_json = move_payload
                move_id = await client.create("account.move", move_payload)
                if isinstance(move_id, list):
                    move_id = move_id[0]
                await client.action("account.move", "action_post", [int(move_id)])
                snapshot_list = await client.read(
                    "account.move",
                    [int(move_id)],
                    fields=["id", "name", "state", "payment_state", "move_type"],
                )
                snapshot = snapshot_list[0] if snapshot_list else {"id": move_id}
                normalized = normalize_move_snapshot(snapshot)
                self.operations.finish_odoo_attempt(
                    attempt,
                    status="SUCCESS",
                    response=normalized,
                    remote_record_id=str(normalized.get("id") or move_id),
                    remote_name=str(normalized.get("name") or ""),
                )
                invoice.odoo_move_id = str(normalized.get("id") or move_id)
                invoice.odoo_move_name = str(normalized.get("name") or "")
                invoice.odoo_sync_state = sync_state_from_snapshot(normalized)
                invoice.odoo_synced_at = utcnow()
                operation.odoo_sync_state = invoice.odoo_sync_state
                self.db.flush()
                self.operations.transition(
                    operation,
                    state="SYNCED_TO_ODOO",
                    title="Documento sincronizado a Odoo",
                    message=str(invoice.odoo_move_name or invoice.odoo_move_id),
                    details=normalized,
                )
                return AccountingSyncResult(status="SYNCED_TO_ODOO", move=normalized)
            except Exception as exc:  # noqa: BLE001
                self.operations.finish_odoo_attempt(attempt, status="FAILED", error_message=str(exc))
                invoice.odoo_sync_state = "FAILED"
                operation.odoo_sync_state = "FAILED"
                self.db.flush()
                self.operations.record_event(
                    operation,
                    status=operation.state,
                    title="Fallo la sincronizacion Odoo",
                    message=str(exc),
                    stage="SYNCING_TO_ODOO",
                )
                return AccountingSyncResult(status="FAILED", reason=str(exc))

    async def _resolve_partner_id(
        self,
        client: OdooJSON2Client,
        domain: list[list[Any]],
        values: dict[str, Any],
    ) -> int:
        partners = await client.search_read("res.partner", domain=domain, fields=["id", "name", "vat"], limit=1)
        if partners:
            return int(partners[0]["id"])
        partner_id = await client.create("res.partner", values)
        if isinstance(partner_id, list):
            return int(partner_id[0])
        return int(partner_id)
