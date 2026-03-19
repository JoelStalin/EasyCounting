from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_nc_type = fields.Boolean(default=False)
    type = fields.Selection(
        selection_add=[('nc_type', 'NC Tipo')],
        ondelete={'product': 'set cash'},
    )

    @api.depends('journal_id', 'split_transactions')
    def _compute_type(self):
        for pm in self:
            if pm.is_nc_type:
                pm.type = 'nc_type'
                continue

            if pm.journal_id.type in {'cash', 'bank'}:
                pm.type = pm.journal_id.type
            else:
                pm.type = 'pay_later'
