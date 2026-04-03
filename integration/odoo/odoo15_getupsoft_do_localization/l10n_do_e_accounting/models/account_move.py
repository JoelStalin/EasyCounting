# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_ecf_invoice = fields.Boolean(
        copy=False,
        default=lambda self: self.env.user.company_id.l10n_do_ecf_issuer
                             and self.env.user.company_id.l10n_do_country_code
                             and self.env.user.company_id.l10n_do_country_code == "DO",
    )
    l10n_do_company_in_contingency = fields.Boolean(
        string="Company in contingency",
        compute="_compute_company_in_contingency",
    )
    l10n_do_ecf_modification_code = fields.Char(string="e-CF Modification Code", copy=False)
    l10n_do_ecf_security_code = fields.Char(string="e-CF Security Code", copy=False)
    l10n_do_ecf_sign_date = fields.Datetime(string="e-CF Sign Date", copy=False)
    l10n_do_electronic_stamp = fields.Char(string="Electronic Stamp", copy=False)

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        for invoice in self:
            ecf_invoices = self.search([("is_ecf_invoice", "=", True)], limit=1)
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        import requests
        import logging
        _logger = logging.getLogger(__name__)

        for move in self.filtered(lambda m: m.is_invoice() and m.l10n_latam_document_type_id and m.l10n_latam_document_type_id.l10n_do_ncf_type):
            try:
                payload = {
                    "tenantId": move.company_id.id,
                    "odooInvoiceId": move.id,
                    "odooInvoiceName": move.name,
                    "issueDate": str(move.invoice_date or fields.Date.today()),
                    "eCfType": move.l10n_latam_document_type_id.l10n_do_ncf_type,
                    "documentNumber": move.name,
                    "issuerRnc": move.company_id.vat,
                    "issuerName": move.company_id.name,
                    "currency": move.currency_id.name or "DOP",
                    "totalAmount": float(move.amount_total),
                    "totalItbis": float(sum(line.price_total - line.price_subtotal for line in move.invoice_line_ids if line.tax_ids)),
                    "totalDiscount": float(sum((line.price_unit * line.quantity) * (line.discount / 100.0) for line in move.invoice_line_ids if not line.display_type)),
                    "buyer": None,
                    "lines": []
                }
                if move.partner_id.vat:
                    payload["buyer"] = {
                        "rnc": move.partner_id.vat,
                        "name": move.partner_id.name
                    }

                for line in move.invoice_line_ids.filtered(lambda l: not l.display_type):
                    payload["lines"].append({
                        "product_name": line.name[:50] if line.name else "Item",
                        "quantity": float(line.quantity),
                        "unit_price": float(line.price_unit),
                        "itbis_rate": 18.0 if line.tax_ids else 0.0,
                        "discount": float(line.discount)
                    })
                
                # Nginx router from WSL
                url = "http://host.docker.internal:28080/api/v1/odoo/invoices/transmit"
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=payload, headers=headers, timeout=5)
                response.raise_for_status()
                _logger.info("Factura %s encolada en Certia. Track ID: %s", move.name, response.json().get('certia_track_id'))
            except Exception as e:
                _logger.error("Error transmitiendo a Certia desde Odoo 15: %s", str(e))
        return res
