import json

from odoo import models, fields


class PosPayment(models.Model):
    _inherit = "pos.payment"

    note = fields.Char()
    credit_note_id = fields.Integer()

    def _export_for_ui(self, payment):
        vals = super()._export_for_ui(payment)
        vals.update({
            'note': payment.note,
            'name': payment.name,
            'credit_note_id': payment.credit_note_id,
        })
        return vals

    def _create_payment_moves(self):
        # TODO: Sin uso, remover en la proxima version.
        result = self.env['account.move']
        cnpm = self.env.ref('l10n_do_pos.credit_note_payment_method')
        nc_pays = self.filtered(lambda x: x.payment_method_id == cnpm)
        invoice = self.pos_order_id.account_move
        if nc_pays and invoice.invoice_outstanding_credits_debits_widget:
            credits_debits = json.loads(
                invoice.invoice_outstanding_credits_debits_widget)

            for payment in nc_pays:
                for p in credits_debits.get('content', []):
                    if int(payment.credit_note_id) == p.get('move_id', 0):
                        payment_move = self.env['account.move'].browse(p['move_id'])
                        payment.write({'account_move_id': payment_move.id})
                        result |= payment_move

        remaining = self - nc_pays
        if remaining:
            result |= super(PosPayment, remaining)._create_payment_moves()

        return result
