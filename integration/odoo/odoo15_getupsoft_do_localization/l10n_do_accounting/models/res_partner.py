import logging
import re

from ..services import dgii_rnc_web
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_l10n_do_dgii_payer_types_selection(self):
        """Return the list of payer types needed in invoices to clasify
        accordingly to DGII requirements."""
        return [
            ("taxpayer", "Contribuyente Fiscal"),
            ("non_payer", "No Contribuyente"),
            ("nonprofit", "Organización sin ánimo de lucro"),
            ("special", "Régimen Especial"),
            ("governmental", "Gubernamental"),
            ("foreigner", "Extranjero/a"),
            ("self", "Empresa del sistema"),
        ]

    def _get_l10n_do_expense_type(self):
        """Return the list of expenses needed in invoices to clasify accordingly to
        DGII requirements."""
        return [
            ("01", _("01 - Personal")),
            ("02", _("02 - Work, Supplies and Services")),
            ("03", _("03 - Leasing")),
            ("04", _("04 - Fixed Assets")),
            ("05", _("05 - Representation")),
            ("06", _("06 - Admitted Deductions")),
            ("07", _("07 - Financial Expenses")),
            ("08", _("08 - Extraordinary Expenses")),
            ("09", _("09 - Cost & Expenses part of Sales")),
            ("10", _("10 - Assets Acquisitions")),
            ("11", _("11 - Insurance Expenses")),
        ]

    @api.model
    def _default_country_id(self):
        return (
            self.env.user.company_id.country_id == self.env.ref("base.do")
            and self.env.ref("base.do")
            or False
        )

    l10n_do_dgii_tax_payer_type = fields.Selection(
        selection="_get_l10n_do_dgii_payer_types_selection",
        compute="_compute_l10n_do_dgii_payer_type",
        inverse="_inverse_l10n_do_dgii_tax_payer_type",
        string="Taxpayer Type",
        index=True,
        store=True,
    )

    l10n_do_expense_type = fields.Selection(
        selection="_get_l10n_do_expense_type",
        string="Cost & Expense Type",
        store=True,
    )

    country_id = fields.Many2one(default=_default_country_id)

    # ----------
    # COMPUTES
    # ----------

    @api.depends("vat", "country_id", "name")
    def _compute_l10n_do_dgii_payer_type(self):
        """Compute the type of partner depending on soft decisions"""
        company_id = self.env["res.company"].search(
            [("id", "=", self.env.user.company_id.id)]
        )
        for partner in self:
            if partner.id == company_id.partner_id.id:
                partner.l10n_do_dgii_tax_payer_type = "self"
                continue

            vat = str(partner.vat if partner.vat else partner.name)
            is_dominican_partner = bool(partner.country_id == self.env.ref("base.do"))

            if partner.country_id and not is_dominican_partner:
                partner.l10n_do_dgii_tax_payer_type = "foreigner"

            elif vat and (
                not partner.l10n_do_dgii_tax_payer_type
                or partner.l10n_do_dgii_tax_payer_type == "non_payer"
            ):
                if partner.country_id and is_dominican_partner:
                    if vat.isdigit() and len(vat) == 9:
                        if not partner.vat:
                            partner.vat = vat
                        if partner.name and "MINISTERIO" in partner.name:
                            partner.l10n_do_dgii_tax_payer_type = "governmental"
                        elif partner.name and any(
                            [n for n in ("IGLESIA", "ZONA FRANCA") if n in partner.name]
                        ):
                            partner.l10n_do_dgii_tax_payer_type = "special"
                        elif vat.startswith("1"):
                            partner.l10n_do_dgii_tax_payer_type = "taxpayer"
                        elif vat.startswith("4"):
                            partner.l10n_do_dgii_tax_payer_type = "nonprofit"
                        else:
                            partner.l10n_do_dgii_tax_payer_type = "taxpayer"

                    elif len(vat) == 11:
                        if vat.isdigit():
                            if not partner.vat:
                                partner.vat = vat
                            partner.l10n_do_dgii_tax_payer_type = "taxpayer"
                        else:
                            partner.l10n_do_dgii_tax_payer_type = "non_payer"
                    else:
                        partner.l10n_do_dgii_tax_payer_type = "non_payer"
            elif not partner.l10n_do_dgii_tax_payer_type:
                partner.l10n_do_dgii_tax_payer_type = "non_payer"
            else:
                partner.l10n_do_dgii_tax_payer_type = (
                    partner.l10n_do_dgii_tax_payer_type
                )

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

    # -----------
    # CRUD
    # -----------

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for reg in res.filtered(lambda p: not p.property_account_position_id):
            reg._set_position_fiscal()
            # fpos = self.sudo().env['account.fiscal.position'].get_fiscal_position(re.id)
            # if fpos:
            #     re.property_account_position_id = fpos.id
        return res

    # -----------
    # ONCHANGES
    # -----------

    @api.onchange("vat", "country_id")
    def _set_position_fiscal(self):
        try:
            if self.vat and self.country_id:
                if self.country_id.id == self.env.ref("base.do").id:
                    if len(self.vat) == 9:
                        self.property_account_position_id = self.env.ref(
                            "l10n_do.position_service_moral", raise_if_not_found=False
                        ).id if self.env.ref("l10n_do.position_service_moral", raise_if_not_found=False) else False
                    else:
                        self.property_account_position_id = self.env.ref(
                            "l10n_do_accounting.final_consumer", raise_if_not_found=False
                        ).id if self.env.ref("l10n_do_accounting.final_consumer", raise_if_not_found=False) else False
                else:
                    self.property_account_position_id = self.env.ref(
                        "l10n_do.position_exterior", raise_if_not_found=False
                    ).id if self.env.ref("l10n_do.position_exterior", raise_if_not_found=False) else False
        except Exception:
            pass

    @api.onchange("name", "vat")
    def onchange_partner_name(self):
        if self.vat or self.name:
            val = re.sub(r"[^0-9]", "", self.vat or self.name)

            if val and len(val) in (9, 11):
                valid, dgii_data = self.validate_rnc_cedula(val)

                if valid == 1:
                    self.update(
                        {
                            "vat": dgii_data["vat"],
                            "name": dgii_data["name"],
                            "comment": dgii_data["comment"],
                            "company_type": dgii_data["company_type"],
                        }
                    )
                else:
                    return {}

    # -----------------
    # BUSINESS METHODS
    # -----------------

    @api.model
    def validate_rnc_cedula(self, fiscal_id):
        """
        Validate RNC/Cedula using the new web scraper.
        Returns (success_code, data_or_msg).
        success_code: 1 for success, 0 for failure.
        """
        try:
            dgii_data = dgii_rnc_web.lookup_rnc_cedula(fiscal_id)
            if dgii_data:
                # The scraper returns a dict with 'vat', 'name', 'comment', etc.
                # We return 1 (success) and the data dict.
                return 1, dgii_data
            else:
                return 0, _("RNC/Cédula no encontrado en DGII.")
        except Exception as e:
            _logger.error("Error validando RNC via scraper: %s", e)
            return 0, _("Error de conexión con DGII.")
