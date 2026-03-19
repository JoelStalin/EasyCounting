from odoo import models, fields


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    l10n_do_to_invoice = fields.Boolean(
        string="(POS) default to invoice",
        default=False,
        help="Este es un campo tecnico que le permite seleccionar automaticamente "
             " el boton 'Factura' en el punto de venta al momento de pagar una orden.\n"
             " Y asi poder asegurar que el cliente fiscal siempre obtenga una factura"
             " fiscal."
    )
