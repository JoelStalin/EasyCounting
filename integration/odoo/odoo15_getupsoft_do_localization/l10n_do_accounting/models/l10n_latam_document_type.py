from re import compile

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class L10nLatamDocumentType(models.Model):
    _inherit = "l10n_latam.document.type"

    l10n_do_use_in = fields.Selection(
        [
            ("sale", "Ventas"),
            ("purchase", "Compras"),
            ("both", "Ambos"),
        ],
        string="Use in",
        help="Facilita el filtrado de NCF para los diferente acosos de uso.",
    )
    l10n_do_auto_sequence = fields.Boolean(
        default=False,
        string="Auto sequence",
        help="Tenemos casos de NCF de compras que debemos llevar la secuencia."
        "\n Para dichos casos existe este flag.",
    )

    # -------------------------------------------------------------------------
    # OVERRIDE METHODS
    # -------------------------------------------------------------------------

    def _format_document_number(self, document_number):
        """Make validation of Import Dispatch Number
        * making validations on the document_number.
        * format the document_number against a pattern and return it
        """

        self.ensure_one()
  
        if self.country_id != self.env.ref("base.do"):
            return super()._format_document_number(document_number)

        if not document_number:
            return False

        # NCF/ECF validation regex
        regex = r"^(P?((?=.{13})E)type(\d{10})|(((?=.{11})B))type(\d{8}))$".replace(
            "type", str(self.doc_code_prefix)[1:3]
        )
        pattern = compile(regex)

        if not bool(pattern.match(document_number)):
            raise ValidationError(
                _("NCF %s doesn't have the correct structure") % document_number
            )
        
        return document_number

    # -------------------------------------------------------------------------
    # HELP METHODS
    # -------------------------------------------------------------------------

    def _len_sequence(self):
        self.ensure_one()
        return self.code == "E" and 10 or 8

    def _is_electronic_ncf(self):
        self.ensure_one()
        return self.code == "E"

    def _purchase_ncf_auto_sequence(self):
        """
        Lista de NCF de compras a las que le emitimos secuencia.

        Importante: la siguiente informacion se tomo del siguiente documento
        https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/contribuyentes/facturacion/Documents/Comprobantes%20Fiscales/2-Guia-Informativa-NCF.pdf.

        B11: Comprobantes de Compras

            Este tipo de comprobante deberá ser
            emitido por el comprador para reducir
            costos y gastos cuando adquieran bienes
            y/o servicios de personas no registradas
            como contribuyentes. En este tipo de
            comprobante el comprador debe colocar
            nombre y cédula del vendedor.

        B13 : Comprobante para Gastos Menores

            Este tipo de comprobante debe ser emitido
            por los contribuyentes para sustentar pagos
            realizados por su personal, sean éstos
            efectuados en territorio dominicano o en
            el extranjero, y que estén relacionados
            a su trabajo, como: consumibles,
            pasajes y transporte público, tarifas de
            estacionamiento y peajes.

        B17 : Comprobantes de Pagos al Exterior

            Son los utilizados para efectuar pagos
            a proveedores del exterior de rentas
            gravadas de fuente dominicana a
            Personas Físicas o Jurídicas no residentes
            en el país.
        """
        return self.search([("l10n_do_auto_sequence", "=", True)])
