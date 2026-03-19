import time
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    state = fields.Selection(
        selection_add=[("is_l10n_do_return_order", "Return Order")],
        ondelete={"product": "set invoiced"},
    )

    payment_include_credit_note = fields.Boolean(
        compute="_compute_payment_include_credit_note"
    )
    l10n_latam_document_number = fields.Char("Fiscal Number", copy=False)
    l10n_do_ncf_expiration_date = fields.Date("NCF expiration date", copy=False)
    l10n_do_origin_ncf = fields.Char("Modified NCF", copy=False)
    l10n_do_is_return_order = fields.Boolean(
        string="Return order",
        copy=False,
        default=False,
    )
    l10n_latam_document_type_id = fields.Many2one(
        "l10n_latam.document.type",
        "Document Type",
    )
    l10n_latam_use_documents = fields.Boolean(
        related="config_id.invoice_journal_id.l10n_latam_use_documents",
        depends=["config_id", "config_id.invoice_journal_id"],
    )

    l10n_do_payment_credit_note_ids = fields.One2many(
        "pos.order.payment.credit.note",
        "pos_order_id",
        string="Credit Note payments",
    )

    @api.depends("l10n_do_payment_credit_note_ids")
    def _compute_payment_include_credit_note(self):
        for order in self:
            order.payment_include_credit_note = bool(
                order.l10n_do_payment_credit_note_ids
            )

    @api.model
    def _order_fields(self, ui_order):
        fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get("to_invoice", False):
            fields.update(
                {
                    "l10n_latam_document_number": ui_order[
                        "l10n_latam_document_number"
                    ],
                    "l10n_do_ncf_expiration_date": ui_order.get(
                        "l10n_do_ncf_expiration_date", ""
                    ),  # noqa: E501
                    "l10n_do_origin_ncf": ui_order.get("l10n_do_origin_ncf", ""),
                    "l10n_do_is_return_order": ui_order.get(
                        "l10n_do_is_return_order", False
                    ),  # noqa: E501
                    "l10n_latam_document_type_id": ui_order.get(
                        "l10n_latam_document_type_id", False
                    ),  # noqa: E501
                }
            )
        return fields

    def _apply_creadit_note_payments(self):
        """Reconcile Credit Notes."""
        if self.payment_include_credit_note:
            receivable_account = (
                self.env["res.partner"]
                ._find_accounting_partner(self.partner_id)
                .property_account_receivable_id
            )

            invoice_rec_line = self.account_move.line_ids.filtered(
                lambda line: line.debit > 0 and line.account_id == receivable_account
            )

            time.sleep(0.5)

            for move in self.l10n_do_payment_credit_note_ids.mapped('account_move_id'):
                # self.account_move = credit_note.account_move_id.id
                credit_note_rec_line = move.line_ids.filtered(
                    lambda l: l.account_id == receivable_account
                )
                to_reconcile = invoice_rec_line | credit_note_rec_line
                to_reconcile.sudo().reconcile()

    def _apply_invoice_payments(self):
        # OVERRITE
        self.l10n_latam_document_number = self.account_move.l10n_latam_document_number
        self.l10n_do_ncf_expiration_date = self.account_move.l10n_do_ncf_expiration_date

        if not self.l10n_do_is_return_order:
            super(PosOrder, self)._apply_invoice_payments()

        self._apply_creadit_note_payments()

    def _export_for_ui(self, order):
        order_ui = super(PosOrder, self)._export_for_ui(order)
        order_ui.update(
            {
                "l10n_latam_document_number": order.l10n_latam_document_number,
                "l10n_do_ncf_expiration_date": order.l10n_do_ncf_expiration_date,
                "l10n_do_origin_ncf": order.l10n_do_origin_ncf,
                "l10n_latam_document_type_id": order.l10n_latam_document_type_id.id,
                "l10n_do_is_return_order": order.l10n_do_is_return_order,
            }
        )
        return order_ui

    def _is_pos_order_paid(self):
        if self.filtered(
            lambda order: order.l10n_latam_use_documents
            and order.l10n_do_is_return_order
        ):
            return True
        return super(PosOrder, self)._is_pos_order_paid()

    def action_pos_order_paid(self):
        self.ensure_one()

        if self.l10n_do_is_return_order:
            self.write({"state": "paid"})
            return True

        return super().action_pos_order_paid()

    def add_payment(self, data):
        self.ensure_one()

        cnpm = self.env.ref("getupsoft_l10n_do_pos.credit_note_payment_method")
        if data["payment_method_id"] == cnpm.id:
            credit_note = (
                self.env["pos.order"]
                .search([("l10n_latam_document_number", "=", data["note"])])
                .account_move
            )
            self.env["pos.order.payment.credit.note"].create(
                {
                    "amount": data["amount"],
                    "account_move_id": credit_note.id,
                    "pos_order_id": data["pos_order_id"],
                    "name": data["note"],
                }
            )
        elif not self.l10n_do_is_return_order:
            super(PosOrder, self).add_payment(data)

        self.amount_paid = sum(self.payment_ids.mapped("amount")) + sum(
            self.l10n_do_payment_credit_note_ids.mapped("amount")
        )

    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        for order in self:
            if order.l10n_do_is_return_order:
                order.sudo().write({"state": "is_l10n_do_return_order"})

            # Reconcile Credit Notes
            receivable_account = (
                self.env["res.partner"]
                ._find_accounting_partner(self.partner_id)
                .property_account_receivable_id
            )

            invoice_rec_line = order.account_move.line_ids.filtered(
                lambda line: line.debit > 0 and line.account_id == receivable_account
            )

            for credit_note in order.l10n_do_payment_credit_note_ids:
                order.account_move = credit_note.account_move_id.id
                credit_note_rec_line = credit_note.account_move_id.line_ids.filtered(
                    lambda l: l.account_id == receivable_account
                )
                to_reconcile = invoice_rec_line | credit_note_rec_line
                to_reconcile.sudo().reconcile()
        return res

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        super(PosOrder, self)._process_payment_lines(
            pos_order, order, pos_session, draft
        )
        order.amount_paid = sum(order.payment_ids.mapped("amount")) + sum(
            order.l10n_do_payment_credit_note_ids.mapped("amount")
        )
        if sum(order.payment_ids.mapped("amount")) < 0:
            order.payment_ids.unlink()

    def _prepare_invoice_vals(self):
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()
        documents = self.config_id.invoice_journal_id.l10n_latam_use_documents
        if documents and self.to_invoice:
            invoice_vals["l10n_latam_document_number"] = self.l10n_latam_document_number
            invoice_vals[
                "l10n_latam_document_type_id"
            ] = self.l10n_latam_document_type_id.id  # noqa: E501
            if self.l10n_do_is_return_order:
                invoice_vals["move_type"] = "out_refund"
                invoice_vals["l10n_do_origin_ncf"] = self.l10n_do_origin_ncf
        return invoice_vals

    @api.model
    def credit_note_info_from_ui(self, ncf):
        # TODO: CHECK WTF l10n_latam_document_number cant filter
        out_refund_invoice = (
            self.env["pos.order"]
            .search(
                [
                    ("l10n_latam_document_number", "=", ncf),
                    ("l10n_do_is_return_order", "=", True),
                ]
            )
            .account_move
        )
        return {
            "id": out_refund_invoice.id,
            "residual": out_refund_invoice.amount_residual,
            "partner_id": out_refund_invoice.partner_id.id,
        }

    def get_nc_line_from_ui(self, client_id):
        ncLines = self.env["account.move"].search(
            [
                ("partner_id", "=", client_id),
                ("move_type", "=", "out_refund"),
                ("amount_residual", ">", 0),
                ("state", "=", "posted"),
            ]
        )
        return [
            {
                "label": f"{line.name} ($ {line.amount_residual})",
                "isSelected": False,
                "id": line.id,
                "item": {
                    "id": line.id,
                    "residual": line.amount_residual,
                    "name": line.name,
                },
            }
            for line in ncLines
        ]

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        res.update(
            {
                "note": ui_paymentline.get("note"),
                "credit_note_id": ui_paymentline.get("credit_note_id"),
            }
        )
        return res

    # def _prepare_refund_values(self, current_session):
    #     vals = super(PosOrder, self)._prepare_refund_value(current_session)
    #     if self.l10n_latam_document_type_id:
    #         ncf_nc_type = self.env.ref('getupsoft_l10n_do_accounting.ncf_credit_note_client')
    #         vals.update({
    #             'l10n_latam_document_type_id': ncf_nc_type.id,
    #             'l10n_do_is_return_order': True,
    #             'l10n_do_origin_ncf': self.l10n_latam_document_number,
    #         })
    #     return vals

    def _get_fields_for_draft_order(self):
        fields = super(PosOrder, self)._get_fields_for_draft_order()
        fields.extend(
            [
                "l10n_do_origin_ncf",
                "l10n_do_is_return_order",
                "l10n_latam_document_number",
                "l10n_latam_document_type_id",
                "fiscal_position_id",
                "to_invoice",
            ]
        )
        return fields


class PosOrderPaymentCreditNote(models.Model):
    _name = "pos.order.payment.credit.note"
    _rec_name = "name"
    _description = "POS Credit Notes"

    name = fields.Char()
    amount = fields.Monetary()
    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Credit note",
        required=False,
    )
    currency_id = fields.Many2one(
        related="account_move_id.currency_id",
    )
    pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        string="order",
        required=False,
    )
