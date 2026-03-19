from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError, AccessError


class AccountMove(models.Model):
    _inherit = "account.move"
    _sequence_fixed_regex = r"^(?P<prefix1>.*?)(?P<seq>\d{0,8})(?P<suffix>\D*?)$"

    l10n_do_ncf_is_required = fields.Boolean(compute="_compute_l10n_do_ncf_is_required")
    l10n_do_ncf_expiration_date = fields.Date(string="Valid until")
    l10n_latam_manual_document_number = fields.Boolean(store=True)

    def _get_l10n_do_cancellation_type(self):
        """Return the list of cancellation types required by DGII."""
        return [
            ("01", _("01 - Pre-printed Invoice Impairment")),
            ("02", _("02 - Printing Errors (Pre-printed Invoice)")),
            ("03", _("03 - Defective Printing")),
            ("04", _("04 - Correction of Product Information")),
            ("05", _("05 - Product Change")),
            ("06", _("06 - Product Return")),
            ("07", _("07 - Product Omission")),
            ("08", _("08 - NCF Sequence Errors")),
            ("09", _("09 - For Cessation of Operations")),
            ("10", _("10 - Lossing or Hurting Of Counterfoil")),
        ]

    l10n_do_cancellation_type = fields.Selection(
        selection="_get_l10n_do_cancellation_type",
        string="Cancellation Type",
        copy=False,
    )

    # DGII Reports

    def _get_l10n_do_income_type(self):
        """Return the list of income types required by DGII."""
        return [
            ("01", _("01 - Operational Incomes")),
            ("02", _("02 - Financial Incomes")),
            ("03", _("03 - Extraordinary Incomes")),
            ("04", _("04 - Leasing Incomes")),
            ("05", _("05 - Income for Selling Depreciable Assets")),
            ("06", _("06 - Other Incomes")),
        ]

    l10n_do_expense_type = fields.Selection(
        selection=lambda self: self.env["res.partner"]._get_l10n_do_expense_type(),
        string="Cost & Expense Type",
    )
    l10n_do_income_type = fields.Selection(
        selection="_get_l10n_do_income_type",
        string="Income Type",
        copy=False,
        default=lambda self: self._context.get("l10n_do_income_type", "01"),
    )
    l10n_do_origin_ncf = fields.Char(string="Modifies")

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("move_type", "company_id")
    def _compute_l10n_do_ncf_is_required(self):
        for move in self:
            move.l10n_do_ncf_is_required = (
                move.country_code == "DO" and move.journal_id.l10n_latam_use_documents
            )

    # -------------------------------------------------------------------------
    # OVERRIDE METHODS
    # -------------------------------------------------------------------------

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if (
            self.company_id.country_id == self.env.ref("base.do")
            and self.l10n_latam_document_type_id
            and self.move_type == "in_invoice"
            and self.partner_id
        ):
            self.l10n_do_expense_type = (
                self.partner_id.l10n_do_expense_type
                if not self.l10n_do_expense_type
                else self.l10n_do_expense_type
            )

        return super(AccountMove, self)._onchange_partner_id()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()

        if not (
            self.journal_id.l10n_latam_use_documents
            and self.journal_id.company_id.country_id == self.env.ref("base.do")
        ):
            return super()._get_l10n_latam_documents_domain()

        if self.debit_origin_id:
            return [("internal_type", "=", "debit_note")]

        internal_types = ["debit_note"]
        ncf_domain = ()
        if self.move_type in ["out_refund", "in_refund"]:
            internal_types.append("credit_note")
        else:
            internal_types.append("invoice")

            if (
                self.partner_id.commercial_partner_id.property_account_position_id
                and self.partner_id.commercial_partner_id.property_account_position_id.l10n_do_ncf_ids
            ):
                ncf_domain = (
                    "doc_code_prefix",
                    "in",
                    self.partner_id.commercial_partner_id.property_account_position_id.l10n_do_ncf_ids.mapped(
                        "doc_code_prefix"
                    ),
                )
            else:
                # TODO: que hacer si no tiene posicion fiscal ?,

                # si es extranjero le colocamos los ncf adecuados
                if self.partner_id.commercial_partner_id.country_id != self.env.ref(
                    "base.do"
                ):
                    ncf_domain = ("doc_code_prefix", "in", ("B16", "B17"))
                # si no lo es, le tratamos como consumirdor final/proveedor informal
                else:
                    ncf_domain = ("doc_code_prefix", "in", ("B02", "B11"))

        domain = [
            ("internal_type", "in", internal_types),
            ("country_id", "=", self.company_id.country_id.id),
        ]

        if (
            ncf_domain
            and self.partner_id.commercial_partner_id != self.env.company.partner_id
        ):
            domain.append(ncf_domain)

        if self.is_purchase_document():
            domain.append(("l10n_do_use_in", "in", (False, "both", "purchase")))
            # Si es compra y el proveedor es la misma empresa del sistema entonces solo sera un "Gasto Menor"
            if self.partner_id.commercial_partner_id == self.env.company.partner_id:
                domain.append(("doc_code_prefix", "=", "B13"))

        if self.is_sale_document():
            domain.append(("l10n_do_use_in", "in", (False, "both", "sale")))

        return domain

    @api.depends("name")
    def _compute_l10n_latam_document_number(self):
        recs_with_name = self.filtered(
            lambda x: x.name != "/"
            and x.country_code == "DO"
            and x.journal_id.l10n_latam_use_documents
        )
        for rec in recs_with_name:
            rec.l10n_latam_document_number = rec.name
        super(AccountMove, self - recs_with_name)._compute_l10n_latam_document_number()

    @api.onchange("l10n_latam_document_type_id", "l10n_latam_document_number")
    def _inverse_l10n_latam_document_number(self):
        do_invoice = self.filtered(
            lambda x: x.l10n_latam_document_type_id
            and x.country_code == "DO"
            and x.journal_id.l10n_latam_use_documents
        )
        for rec in do_invoice:
            if not rec.l10n_latam_document_number:
                rec.name = "/"
            else:
                l10n_latam_document_number = (
                    rec.l10n_latam_document_type_id._format_document_number(
                        rec.l10n_latam_document_number
                    )
                )
                if rec.l10n_latam_document_number != l10n_latam_document_number:
                    rec.l10n_latam_document_number = l10n_latam_document_number
                rec.name = l10n_latam_document_number
        super(AccountMove, self - do_invoice)._inverse_l10n_latam_document_number()

    def _is_manual_document_number(self):
        if self.l10n_latam_document_type_id and self.is_purchase_document():
            # NCF de compra que le vamos a manejar el sequencial
            ncf_control = self.env[
                "l10n_latam.document.type"
            ]._purchase_ncf_auto_sequence()
            prefix = self.l10n_latam_document_type_id.doc_code_prefix
            return (
                self.journal_id.type == "purchase"
                and prefix not in ncf_control.mapped("doc_code_prefix")
            )
        return super()._is_manual_document_number()

    def unlink(self):
        if self.filtered(
            lambda inv: inv.is_purchase_document()
            and inv.country_code == "DO"
            and inv.l10n_latam_use_documents
            and inv.posted_before
        ):
            raise UserError(
                _("You cannot delete fiscal invoice which have been posted before")
            )
        return super(AccountMove, self).unlink()

    def _reverse_move_vals(self, default_values, cancel=True):
        ctx = self.env.context
        amount = ctx.get("amount")
        percentage = ctx.get("percentage")
        refund_type = ctx.get("refund_type")
        reason = ctx.get("reason")

        res = super(AccountMove, self)._reverse_move_vals(
            default_values=default_values, cancel=cancel
        )
        if self.country_code != "DO":
            return res

        if self.country_code == "DO":
            res["l10n_do_origin_ncf"] = self.l10n_latam_document_number

        if refund_type in ("percentage", "fixed_amount"):
            price_unit = (
                amount
                if refund_type == "fixed_amount"
                else self.amount_untaxed * (percentage / 100)
            )
            res["line_ids"] = False
            res["invoice_line_ids"] = [
                (0, 0, {"name": reason or _("Refund"), "price_unit": price_unit})
            ]
        return res

    def button_cancel(self):
        fiscal_invoice = self.filtered(
            lambda inv: inv.country_code == "DO"
            and self.move_type[-6:] in ("nvoice", "refund")
            and inv.l10n_latam_use_documents
        )

        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time.")
            )

        if fiscal_invoice and not self.env.user.has_group(
            "getupsoft_l10n_do_accounting.group_l10n_do_fiscal_invoice_cancel"
        ):
            raise AccessError(_("You are not allowed to cancel Fiscal Invoices"))

        if fiscal_invoice and not fiscal_invoice.is_purchase_document():
            action = self.env.ref(
                "getupsoft_l10n_do_accounting.action_account_move_cancel"
            ).read()[0]
            action["context"] = {"default_move_id": fiscal_invoice.id}
            return action

        return super(AccountMove, self).button_cancel()

    def action_reverse(self):
        fiscal_invoice = self.filtered(
            lambda inv: inv.country_code == "DO"
            and self.move_type[-6:] in ("nvoice", "refund")
        )
        if fiscal_invoice and not self.env.user.has_group(
            "getupsoft_l10n_do_accounting.group_l10n_do_fiscal_credit_note"
        ):
            raise AccessError(_("You are not allowed to issue Fiscal Credit Notes"))

        return super(AccountMove, self).action_reverse()

    # -------------------------------------------------------------------------
    # SEQUENCE HACK
    # -------------------------------------------------------------------------

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed)

        if self.l10n_do_ncf_is_required:
            where_string = where_string.replace(
                "AND sequence_prefix !~ %(anti_regex)s ", ""
            )
            where_string = where_string.replace("journal_id = %(journal_id)s AND", "")
            where_string += (
                " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s AND"
                " company_id = %(company_id)s"
            )
            if (
                not self.l10n_latam_manual_document_number
                and self.move_type != "in_refund"
            ):
                where_string += " AND move_type = %(move_type)s"
                param["move_type"] = self.move_type
            else:
                where_string += " AND l10n_latam_manual_document_number = 'f'"

            param["company_id"] = self.company_id.id or False
            param["l10n_latam_document_type_id"] = (
                self.l10n_latam_document_type_id.id or 0
            )
        return where_string, param

    def _get_starting_sequence(self):
        if self.l10n_do_ncf_is_required and self.l10n_latam_document_type_id:
            document_type_id = self.l10n_latam_document_type_id
            return "%s%s" % (
                document_type_id.doc_code_prefix,
                "".zfill(document_type_id._len_sequence()),
            )

        return super()._get_starting_sequence()

    #@api.constrains('name', 'journal_id', 'state')
    #def _check_unique_sequence_number(self):
    #    pass

    def _post(self, soft=True):
        res = super()._post(soft)


        l10n_do_invoices = self.filtered(
            lambda inv: inv.company_id.country_id == self.env.ref("base.do")
            and inv.l10n_latam_use_documents
        )

        for invoice in l10n_do_invoices.filtered(
            lambda inv: inv.l10n_latam_document_type_id
        ):
            
            if invoice.l10n_latam_document_type_id.doc_code_prefix  not in ("B02", "E32"):
                self.check_rnc_format(invoice.partner_id.vat)
        
            ncf_control = invoice.journal_id.l10n_do_ncf_control_manager_ids.filtered(
                lambda x: x.l10n_latam_document_type_id
                == invoice.l10n_latam_document_type_id
            )
            if not ncf_control:
                raise ValidationError("NCF Control no encontrado")

            invoice.l10n_do_ncf_expiration_date = (
                ncf_control.l10n_do_ncf_expiration_date
            )

        non_payer_type_invoices = l10n_do_invoices.filtered(
            lambda inv: not inv.partner_id.property_account_position_id
        )
        if non_payer_type_invoices:
            raise ValidationError(_("Fiscal invoices require partner fiscal type"))

        return res

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.country_code == "DO":
            return "getupsoft_l10n_do_accounting.report_invoice_document_inherited"
        return super()._get_name_invoice_report()

    # -------------------------------------------------------------------------
    # CONSTRAINS
    # -------------------------------------------------------------------------

    @api.constrains("name")
    def _check_limit_ncf(self):
        for last_invoice in self.filtered(lambda x: x._is_last_from_seq_chain()):
            if (
                last_invoice
                and isinstance(last_invoice.name, str)
                and last_invoice.name
                and last_invoice.name != "/"
                and last_invoice.journal_id
            ):
                ncf_control = (
                    last_invoice.journal_id.l10n_do_ncf_control_manager_ids.filtered(
                        lambda x: x.l10n_latam_document_type_id
                        == last_invoice.l10n_latam_document_type_id
                    )
                )

                if (
                    ncf_control
                    and int(last_invoice.name[3:]) - ncf_control.l10n_do_ncf_max_number
                    == 1
                ):
                    raise ValidationError(
                        _(
                            "Numero maximo de NCF alcanzado para '%s'",
                            ncf_control.l10n_latam_document_type_id.name,
                        )
                    )

        return True


    def check_rnc_format(self, vat):
        if vat  == "" or not vat:
            raise ValidationError(
                _("Este tipo de factura requiere un/a RNC/Cédula  para poder ser confirmada.  Por favor, revisar los datos del cliente/proveedor.")
            )


        if not vat or not str(vat).isdigit() or len(vat) not in (9, 11):
            raise ValidationError(
                _("El RNC/Cédula no es valido para el tipo de factura actual.")
            )
