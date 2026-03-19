from odoo import models, fields


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    l10n_do_to_invoice = fields.Boolean(default=False)


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _get_fp_vals(self, company, position):
        data = super()._get_fp_vals(company, position)
        data.update({"l10n_do_to_invoice": position.l10n_do_to_invoice or False})
        return data
