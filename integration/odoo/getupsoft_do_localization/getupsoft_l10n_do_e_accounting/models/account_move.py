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

    @api.depends("company_id", "company_id.l10n_do_ecf_issuer")
    def _compute_company_in_contingency(self):
        for invoice in self:
            ecf_invoices = self.search([("is_ecf_invoice", "=", True)], limit=1)
            invoice.l10n_do_company_in_contingency = bool(
                ecf_invoices and not invoice.company_id.l10n_do_ecf_issuer
            )
