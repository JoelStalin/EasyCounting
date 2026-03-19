from odoo import models, fields


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    l10n_do_ncf_ids = fields.Many2many("l10n_latam.document.type", string="NCF Types")


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _get_fp_vals(self, company, position):
        data = super()._get_fp_vals(company, position)
        data.update({"l10n_do_ncf_ids": position.l10n_do_ncf_ids or False})
        return data
