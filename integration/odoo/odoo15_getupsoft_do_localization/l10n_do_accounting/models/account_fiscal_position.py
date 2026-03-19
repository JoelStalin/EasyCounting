from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    l10n_do_ncf_type = fields.Selection(
        [
            ("B11", "Comprobantes de Compras"),
            ("B13", "Comprobante para Gastos Menores"),
            ("B14", "Comprobante para Regímenes Especiales"),
            ("B15", "Comprobantes Gubernamentales"),
        ],
        "Tipo de NCF",
    )
    l10n_do_ncf_ids = fields.Many2many("l10n_latam.document.type", string="NCF Types")
