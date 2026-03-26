"""Mappings from local invoices to Odoo accounting payloads."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.accounting import TenantSettings
from app.models.invoice import Invoice, InvoiceLine


def _command_create(values: dict[str, Any]) -> list[Any]:
    return [0, 0, values]


def _decimal(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


def build_partner_domain(invoice: Invoice) -> list[list[Any]]:
    vat = invoice.rnc_receptor or ""
    if vat:
        return [["vat", "=", vat]]
    return [["name", "=", invoice.receptor_nombre or "Consumidor final"]]


def build_partner_values(invoice: Invoice, settings: TenantSettings) -> dict[str, Any]:
    vat = invoice.rnc_receptor or None
    if vat and settings.odoo_partner_vat_prefix and not vat.startswith(settings.odoo_partner_vat_prefix):
        vat = f"{settings.odoo_partner_vat_prefix}{vat}"
    return {
        "name": invoice.receptor_nombre or "Consumidor final",
        "vat": vat,
        "street": invoice.receptor_direccion,
        "city": invoice.receptor_municipio,
        "state_id": False,
        "country_id": False,
        "is_company": True if invoice.rnc_receptor else False,
    }


def _line_tax_commands(line: InvoiceLine, settings: TenantSettings) -> list[list[Any]]:
    if (line.itbis_amount or Decimal("0")) > 0 and getattr(settings, "odoo_sales_tax_id", None):
        return [[6, 0, [int(settings.odoo_sales_tax_id)]]]
    if getattr(settings, "odoo_zero_tax_id", None):
        return [[6, 0, [int(settings.odoo_zero_tax_id)]]]
    return []


def build_move_lines(invoice: Invoice, settings: TenantSettings) -> list[list[Any]]:
    lines: list[list[Any]] = []
    if not invoice.line_items:
        lines.append(
            _command_create(
                {
                    "name": invoice.encf,
                    "quantity": 1.0,
                    "price_unit": _decimal(invoice.total),
                }
            )
        )
        return lines

    for line in invoice.line_items:
        values: dict[str, Any] = {
            "name": line.descripcion,
            "quantity": _decimal(line.cantidad),
            "price_unit": _decimal(line.precio_unitario),
            "discount": _decimal(line.discount_amount),
        }
        tax_commands = _line_tax_commands(line, settings)
        if tax_commands:
            values["tax_ids"] = tax_commands
        lines.append(_command_create(values))
    return lines


def _document_type_id(invoice: Invoice, settings: TenantSettings) -> int | None:
    tipo = (invoice.tipo_ecf or "").upper()
    if tipo in {"E31", "E32", "E33", "E34", "B01", "B02", "B03", "B11", "B12", "B13", "B14", "B15", "B16", "B17"}:
        return settings.odoo_customer_document_type_id
    if tipo in {"E43", "E44"}:
        return settings.odoo_credit_note_document_type_id
    if tipo in {"E45", "E46", "E47"}:
        return settings.odoo_debit_note_document_type_id
    return settings.odoo_customer_document_type_id


def build_move_payload(invoice: Invoice, settings: TenantSettings, *, partner_id: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "move_type": "out_invoice",
        "partner_id": partner_id,
        "invoice_date": invoice.fecha_emision.date().isoformat(),
        "invoice_line_ids": build_move_lines(invoice, settings),
        "ref": invoice.encf,
    }
    if settings.odoo_sales_journal_id:
        payload["journal_id"] = settings.odoo_sales_journal_id
    if settings.odoo_company_id:
        payload["company_id"] = settings.odoo_company_id
    if settings.odoo_fiscal_position_id:
        payload["fiscal_position_id"] = settings.odoo_fiscal_position_id
    if settings.odoo_payment_term_id:
        payload["invoice_payment_term_id"] = settings.odoo_payment_term_id
    if settings.odoo_currency_id:
        payload["currency_id"] = settings.odoo_currency_id
    document_type_id = _document_type_id(invoice, settings)
    if document_type_id:
        payload["l10n_latam_document_type_id"] = document_type_id
    return payload

