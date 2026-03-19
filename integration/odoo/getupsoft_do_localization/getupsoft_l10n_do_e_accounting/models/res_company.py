from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_do_ecf_issuer = fields.Boolean("Es emisor electrónico")
    l10n_do_country_code = fields.Char(related="country_id.code", string="Country Code")
