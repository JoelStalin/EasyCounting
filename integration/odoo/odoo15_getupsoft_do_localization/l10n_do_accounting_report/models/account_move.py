"""file: account_move.py ."""
import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class InvoiceServiceTypeDetail(models.Model):
    """Almacena los detalles de servicios."""

    _name = "invoice.service.type.detail"
    _description = "Invoice Service Type Detail"

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ("code_unique", "unique(code)", _("Code must be unique")),
    ]


class AccountMove(models.Model):
    """Agregar logica para el reporte DGII."""

    _inherit = "account.move"

    # 606
    service_total_amount = fields.Monetary(
        compute="_compute_amount_fields",
        store=True,
        currency_field="company_currency_id",
    )
    good_total_amount = fields.Monetary(
        compute="_compute_amount_fields",
        store=True,
        currency_field="company_currency_id",
    )

    invoiced_itbis = fields.Monetary(
        compute="_compute_invoiced_itbis",
        store=True,
        currency_field="company_currency_id",
    )

    withholded_itbis = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    income_withholding = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    third_withheld_itbis = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )
    third_income_withholding = fields.Monetary(
        compute="_compute_withheld_taxes",
        store=True,
        currency_field="company_currency_id",
    )

    payment_date = fields.Date(
        compute="_compute_taxes_fields",
        store=True,
    )
    proportionality_tax = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    cost_itbis = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    selective_tax = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    other_taxes = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )
    legal_tip = fields.Monetary(
        compute="_compute_taxes_fields",
        store=True,
        currency_field="company_currency_id",
    )

    advance_itbis = fields.Monetary(
        compute="_compute_advance_itbis",
        store=True,
        currency_field="company_currency_id",
    )

    isr_withholding_type = fields.Char(
        compute="_compute_isr_withholding_type",
        store=True,
        size=2,
    )

    payment_form = fields.Selection(
        [
            ("01", "Cash"),
            ("02", "Check / Transfer / Deposit"),
            ("03", "Credit Card / Debit Card"),
            ("04", "Credit"),
            ("05", "Swap"),
            ("06", "Credit Note"),
            ("07", "Mixed"),
        ],
        compute="_compute_in_invoice_payment_form",
        store=True,
    )

    is_exterior = fields.Boolean(compute="_compute_is_exterior", store=True)
    service_type = fields.Selection(
        [
            ("01", "Gastos de Personal"),
            ("02", "Gastos por Trabajos, Suministros y Servicios"),
            ("03", "Arrendamientos"),
            ("04", "Gastos de Activos Fijos"),
            ("05", "Gastos de Representación"),
            ("06", "Gastos Financieros"),
            ("07", "Gastos de Seguros"),
            ("08", "Gastos por Regalías y otros Intangibles"),
        ]
    )
    service_type_detail = fields.Many2one("invoice.service.type.detail")
    fiscal_status = fields.Selection(
        [
            ("normal", "Partial"),
            ("done", "Reported"),
            ("blocked", "Not Sent"),
        ],
        copy=False,
        help="* The 'Grey' status means invoice isn't fully reported and may appear "
        "in other report if a withholding is applied.\n"
        "* The 'Green' status means invoice is fully reported.\n"
        "* The 'Red' status means invoice is included in a non sent DGII report.\n"
        "* The blank status means that the invoice have"
        "not been included in a report.",
    )

    amount_with_isr_withholding = fields.Monetary()

    # ----------------------------------------------------------------------------------
    # BUSINESS METHODS
    # ----------------------------------------------------------------------------------

    @api.model
    def norma_recompute(self):
        """
        Logica de recarculo.

        Este método agrega todos los campos de cálculo en []env
        add_todo y luego volver a calcular todos los campos de cálculo
        en caso de que cambie la configuración de dgii y necesite volver a calcular.

        :return:
        """
        records = self.browse(self._context.get("active_ids", self.ids or []))
        for k, v in self.fields_get().items():
            if v.get("store") and v.get("depends"):
                self.env.add_to_compute(self._fields[k], records)
        self.recompute()

    # ----------------------------------------------------------------------------------
    # COMPUTED METHODS
    # ----------------------------------------------------------------------------------

    @api.depends("invoice_line_ids", "invoice_line_ids.product_id", "state")
    def _compute_amount_fields(self):
        """Compute Purchase amount by product type."""
        for inv in self.filtered(
            lambda x: x.move_type in ["in_invoice", "in_refund"] and x.state != "draft"
        ):
            service_amount = 0
            good_amount = 0

            for line in inv.invoice_line_ids:
                # Monto calculado en bienes
                if line.product_id.type in ["product", "consu"]:
                    good_amount += line.price_subtotal
                # Si la linea no tiene un producto
                elif not line.product_id:
                    service_amount += line.price_subtotal
                # Monto calculado en servicio
                else:
                    service_amount += line.price_subtotal

            inv.service_total_amount = inv._convert_to_local_currency(service_amount)
            inv.good_total_amount = inv._convert_to_local_currency(good_amount)

    @api.depends("state")
    def _compute_invoiced_itbis(self):
        """Compute invoice invoiced_itbis taking into account the currency."""
        for inv in self.filtered(lambda x: x.state != "draft"):
            amount = 0
            # TODO: invoiced_itbis solo es el 18% itbis, quizas esto pueda mejorarse.
            for tax in inv._get_tax_line_ids().filtered(
                lambda line: line.tax_line_id.amount == 18
            ):
                if inv.move_type in ["out_invoice", "in_refund"]:
                    amount += tax.credit
                elif inv.move_type in ["in_invoice", "out_refund"]:
                    amount += tax.debit
            inv.invoiced_itbis = inv._convert_to_local_currency(amount)

    
    def get_invoiced_itbis(self):
        """get invoice invoiced_itbis taking into account the currency."""
        tax_total = 0
      
        for inv in self.filtered(lambda x: x.state != "draft"):
            amount = 0
            # TODO: invoiced_itbis solo es el 18% itbis, quizas esto pueda mejorarse.
            for tax in inv._get_tax_line_ids().filtered(
                lambda line: line.tax_line_id.amount == 18
            ):
                if inv.move_type in ["out_invoice", "in_refund"]:
                    amount += tax.credit
                elif inv.move_type in ["in_invoice", "out_refund"]:      
                    amount += tax.debit
            tax_total = inv._convert_to_local_currency(amount)
        return tax_total
    @api.depends("line_ids.tax_line_id", "line_ids.tax_ids", "state")
    def _compute_taxes_fields(self):
        """Compute invoice common taxes fields."""
        for inv in self.filtered(lambda x: x.state != "draft"):
            s, o, l, p, c = 0, 0, 0, 0, 0

            for tax in inv._get_tax_line_ids():
                # Monto Impuesto Selectivo al Consumo
                if tax.tax_line_id.tax_group_id.name == "ISC":
                    s += tax.debit

                # Monto Otros Impuestos/Tasas
                elif tax.tax_line_id.tax_group_id.name == "Otros Impuestos":
                    o += tax.debit

                # Monto Propina Legal
                elif tax.tax_line_id.tax_group_id.name == "Propina":
                    l += tax.debit

                # ITBIS sujeto a proporcionalidad
                elif tax.account_id.account_fiscal_type in ["A29", "A30"]:
                    p += tax.debit

                # ITBIS llevado al Costo
                elif tax.account_id.account_fiscal_type == "A51":
                    c += tax.debit

            inv.selective_tax = s
            inv.other_taxes = o
            inv.legal_tip = l
            inv.proportionality_tax = p
            inv.cost_itbis = c

            if inv.move_type == "out_invoice" and any(
                [inv.third_withheld_itbis, inv.third_income_withholding]
            ):
                # Fecha Pago
                inv._compute_invoice_payment_date()
            if inv.move_type == "in_invoice" and any(
                [inv.withholded_itbis, inv.income_withholding]
            ):
                # Fecha Pago
                inv._compute_invoice_payment_date()

    #Kprge
    @api.depends("state", "move_type", "payment_state", "payment_id")
    def _compute_withheld_taxes(self):
        

     
        for inv in self.filtered(
            lambda x: x.state == "posted" and x.payment_state != 'not_paid'
            and x.move_type in ("out_invoice", "in_invoice")
        ):
            # campos para out_invoice por defecto en 0
            inv.third_withheld_itbis = 0
            inv.third_income_withholding = 0

            # Esta logica funciona de la siguiente manera:
            #   Busca los move_id de los pagos y si los account account
            #   su tipo fiscal aplica entonces sumamos sus montos y los  aplicamos.

            # if inv.payment_state in ("paid", "in_payment", "partial"):

            move_ids = [p["move_id"] for p in inv._get_invoice_payment_widget()]
            aml_ids = (
                self.env["account.move"]
                .browse(move_ids)
                .mapped("line_ids")
                .filtered(lambda aml: aml.account_id.account_fiscal_type)
            )

            if aml_ids:
                withheld_itbis, withheld_isr = 0, 0

                for aml in aml_ids:
                    if aml.account_id.account_fiscal_type in ("A34", "A36"):
                        withheld_itbis += (
                            inv.move_type == "out_invoice" and aml.debit or aml.credit
                        )
                    elif aml.account_id.account_fiscal_type in ("ISR", "A38"):
                        withheld_isr += (
                            inv.move_type == "out_invoice" and aml.debit or aml.credit
                        )

                if inv.move_type == "out_invoice":
                    inv.third_withheld_itbis = withheld_itbis
                    inv.third_income_withholding = withheld_isr
                elif inv.move_type == "in_invoice":
                    inv.withholded_itbis = withheld_itbis
                    inv.income_withholding = withheld_isr

            elif inv.move_type == "in_invoice":
                withheld_itbis, withheld_isr = 0, 0

                for tax in inv._get_tax_line_ids():
                    if tax.tax_line_id.purchase_tax_type == "ritbis":
                        withheld_itbis += tax.credit
                    elif tax.tax_line_id.purchase_tax_type == "isr":
                        withheld_isr += tax.credit

                # Monto ITBIS Retenido por impuesto
                inv.withholded_itbis = abs(
                    inv._convert_to_local_currency(withheld_itbis)
                )
                # Monto Retención Renta por impuesto
                inv.income_withholding = abs(
                    inv._convert_to_local_currency(withheld_isr)
                )

    @api.depends("invoiced_itbis", "cost_itbis", "state")
    def _compute_advance_itbis(self):
        for inv in self.filtered(lambda x: x.state != "draft"):
            inv.advance_itbis = inv.invoiced_itbis - inv.cost_itbis

    @api.depends("line_ids", "state", "move_type", "payment_state")
    def _compute_isr_withholding_type(self):
        """
        Compute ISR Withholding Type.

        Keyword / Values:
        01 -- Alquileres
        02 -- Honorarios por Servicios
        03 -- Otras Rentas
        04 -- Rentas Presuntas
        05 -- Intereses Pagados a Personas Jurídicas
        06 -- Intereses Pagados a Personas Físicas
        07 -- Retención por Proveedores del Estado
        08 -- Juegos Telefónicos
        """
        for inv in self.filtered(
            lambda i: i.move_type == "in_invoice"
            and i.state == "posted"
            and i.payment_state in ("paid", "in_payment")
        ):
            # TODO Revisar esta parte de tax_group_id hacer una relacion con el campo
            # isr_retention_tipe y purchase_tax_type a account.account
            tax_l_id = inv._get_tax_line_ids().filtered(
                lambda t: t.tax_line_id.purchase_tax_type == "isr"
            )

            if tax_l_id:  # invoice tax lines use case
                inv.isr_withholding_type = tax_l_id[0].tax_line_id.isr_retention_type
            else:  # in payment/journal entry use case
                aml_ids = (
                    self.env["account.move"]
                    .browse(p["move_id"] for p in inv._get_invoice_payment_widget())
                    .mapped("line_ids")
                    .filtered(lambda aml: aml.account_id.isr_retention_type)
                )
                if aml_ids:
                    inv.isr_withholding_type = aml_ids[0].account_id.isr_retention_type

    def _get_payment_string(self):
        """
        Compute Vendor Bills payment method string.

        Keyword / Values:
        cash        -- Efectivo
        bank        -- Cheques / Transferencias / Depósitos
        card        -- Tarjeta Crédito / Débito
        credit      -- Compra a Crédito
        swap        -- Permuta
        credit_note -- Notas de Crédito
        mixed       -- Mixto
        """
        self.ensure_one()

        payments = []
        p_string = ""

        for payment in self._get_invoice_payment_widget():
            payment_id = self.env["account.payment"].browse(
                payment.get("account_payment_id")
            )
            move_id = False
            if payment_id:
                if payment_id.journal_id.type in ["cash", "bank"]:
                    p_string = payment_id.journal_id.l10n_do_payment_form
            if not payment_id:
                move_id = self.env["account.move"].browse(payment.get("move_id"))
                if move_id:
                    p_string = "swap"
            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id or move_id else "credit_note"
            payments.append(payment)
        methods = {p for p in payments}
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return "mixed"

    @api.depends("payment_state")
    def _compute_in_invoice_payment_form(self):
        payment_dict = {
            "cash": "01",
            "bank": "02",
            "card": "03",
            "credit": "04",
            "swap": "05",
            "credit_note": "06",
            "mixed": "07",
        }
        invoices_paid = self.filtered(
            lambda x: x.payment_state in ("paid", "in_payment")
        )
        for inv in invoices_paid:
            inv.payment_form = payment_dict.get(inv._get_payment_string(), "04")

        (self - invoices_paid).payment_form = "04"

    @api.depends("l10n_latam_document_type_id")
    def _compute_is_exterior(self):
        external_invs = self.filtered(
            lambda inv: inv.l10n_latam_document_type_id.doc_code_prefix
            in ("B17", "E47")
        )
        external_invs.is_exterior = True
        (self - external_invs).is_exterior = False

    def _compute_invoice_payment_date(self):
        for inv in self.filtered(lambda x: x.state == "posted"):
            dates = [
                payment["date"] for payment in inv._get_reconciled_info_JSON_values()
            ]
            if dates:
                max_date = max(dates)
                date_invoice = inv.invoice_date
                inv.payment_date = (
                    max_date if max_date >= date_invoice else date_invoice
                )

    # ----------------------------------------------------------------------------------
    # CONSTRAINS
    # ----------------------------------------------------------------------------------

    @api.constrains("line_ids")
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice."""
        for inv in self:
            line = [
                tax_line.tax_line_id.purchase_tax_type
                for tax_line in inv._get_tax_line_ids()
                if tax_line.tax_line_id
                and tax_line.tax_line_id.purchase_tax_type in ["isr", "ritbis"]
            ]
            if len(line) != len(set(line)):
                raise ValidationError(
                    _("An invoice cannot have multiple" "withholding taxes.")
                )

    # ----------------------------------------------------------------------------------
    # ONCHANGE METHODS
    # ----------------------------------------------------------------------------------

    @api.onchange("service_type")
    def _onchange_service_type(self):
        self.service_type_detail = False
        return {
            "domain": {"service_type_detail": [("parent_code", "=", self.service_type)]}
        }

    @api.onchange("journal_id")
    def _ext_onchange_journal_id(self):
        self.service_type = False
        self.service_type_detail = False

    # ----------------------------------------------------------------------------------
    # PRIVATE METHODS
    # ----------------------------------------------------------------------------------

    def _get_invoice_payment_widget(self):
        self.ensure_one()
        j = json.loads(self.invoice_payments_widget)
        return j["content"] if j else []

    def _get_tax_line_ids(self):
        self.ensure_one()
        return self.line_ids.filtered("tax_line_id")

    def _convert_to_local_currency(self, amount):
        self.ensure_one()
        sign = -1 if self.move_type in ["in_refund", "out_refund"] else 1
        amount = self.currency_id._convert(
            amount, self.company_id.currency_id, self.company_id, self.date
        )
        return amount * sign

    def _get_payment_move_iterator(self, payment, inv_type, witheld_type):
        payment_id = self.env["account.payment"].browse(
            payment.get("account_payment_id")
        )
        if payment_id:
            if inv_type == "out_invoice":
                return [
                    move_line.debit
                    for move_line in payment_id.move_line_ids
                    if move_line.account_id.account_fiscal_type in witheld_type
                ]
            return [
                move_line.credit
                for move_line in payment_id.move_line_ids
                if move_line.account_id.account_fiscal_type in witheld_type
            ]

        move_id = self.env["account.move"].browse(payment.get("move_id"))
        if move_id:
            if inv_type == "out_invoice":
                return [
                    move_line.debit
                    for move_line in move_id.line_ids
                    if move_line.account_id.account_fiscal_type in witheld_type
                ]
            return [
                move_line.credit
                for move_line in move_id.line_ids
                if move_line.account_id.account_fiscal_type in witheld_type
            ]

    # ----------------------------------------------------------------------------------
    # OVERWRITE METHODS
    # ----------------------------------------------------------------------------------

    def _compute_amount(self):
        """HACK amount_total.

        Segun nuestro contador <Rafael Aponte> el manejo de la retencion ISR se debe
        efecturar de la siguiente manera.

        ******
        ADICIONAL: SOLICITADO TAMBIEN POR <Rafael Aponte>, que se replicara el mismo proceso para la retenciones 
        ******

        Ej:
            El dia 15 de Julio del 2022 se le realiza la compra de un servicio contable
            a un proveedor X, dicha compra se efectura por monto de:

            Costo del servicio  : 20,000.00
            ITBIS               :  3,600.00
            -------------------------------
            Total               : 23,600.00

            - 100% ITBIS        : -3,600.00
            -  10% ISR          : -2,000.00
            -------------------------------
            Deuda               : 18,000.00

            * Caso, el ISR no se debe aplicar hasta que se realiza el pago, por tanto
            nuestra solucion es sumar el monto del ISR al monto total de la factura,
            quedando la factura con un total de RD$ 20,000.00

            * Reporte, en el mes de Julio se reporta un 606 de esta factura con su
            monto total sin retencion ISR, es decir, RD$ 20,000.00.

            * Caso, llega el mes de Agosto y se procede a pagar esta factura al
            proveedor X, pagando la deuda que es de RD$ 18,000.00 ya que la deuda si
            tiene el ISR aplicado.

            * Reporte, en el mes de Agosto se reporta un 606 de esta factura, esta vez
            con su total mas la fecha de pago, sus retenciones ISR etc.
        """
        res = super()._compute_amount()
        for move in self:
            if move.payment_state not in ("paid", "in_payment"):
                move.amount_total += abs(
                    sum(
                        move.line_ids.filtered(
                            lambda line: line.tax_line_id.purchase_tax_type == "isr" or line.tax_line_id.purchase_tax_type == "ritbis"
                        ).mapped("balance")
                    )
                )
        return res




# class AccountMoveLine(models.Model):
#     """ Cambios necesario a los impuesto de la localizacion"""

#     _inherit = "account.move.line"

#     enabled_to_apply_withholding = fields.Boolean('Habilitado para aplicar retencion', help="los movimientos contable de retencion son aplicables una vez realizado el pago", copy=False)

#     # * Check is the account move line retention is valid for apply
#     def is_valid_tax_retention(self):

#         for record in self:

#             if record.tax_line_id.purchase_tax_type != 'ritbis':
#                 # * Not is a account move line wit retention
#                 return True


#             if record.move_id.payment_state not in ('not_paid'):
#                 return True


#         return False