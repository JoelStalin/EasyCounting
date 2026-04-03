import logging
import re

from odoo import _, api, fields, models

from ..services.dgii_rnc_web import HTTPError, URLError, fetch_json, lookup_rnc_cedula, normalize_fiscal_id

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_local_directory_base_url(self):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("getupsoft_dgii_encf.base_url", default="")
            .strip()
        )
        return base_url.rstrip("/")

    def _lookup_official_fiscal_id(self, fiscal_id):
        try:
            return lookup_rnc_cedula(fiscal_id)
        except (HTTPError, URLError, ValueError):
            _logger.warning(
                "Fallo consulta oficial DGII fiscal_id=%s",
                fiscal_id,
                exc_info=True,
            )
            return None

    def _lookup_local_fiscal_id(self, fiscal_id):
        base_url = self._get_local_directory_base_url()
        if base_url:
            try:
                payload = fetch_json(
                    "{}/api/v1/odoo/rnc/{}".format(base_url, fiscal_id),
                    timeout=5,
                )
                return {
                    "vat": payload["rnc"],
                    "name": payload["name"],
                    "comment": payload.get("comment", ""),
                    "company_type": payload.get(
                        "company_type",
                        "company" if len(fiscal_id) == 9 else "person",
                    ),
                    "is_company": bool(
                        payload.get("is_company", len(fiscal_id) == 9)
                    ),
                }
            except HTTPError as exc:
                if getattr(exc, "code", None) == 404:
                    return None
                _logger.warning(
                    "Fallo consulta local RNC fiscal_id=%s",
                    fiscal_id,
                    exc_info=True,
                )
            except (URLError, ValueError):
                _logger.warning(
                    "Fallo consulta local RNC fiscal_id=%s",
                    fiscal_id,
                    exc_info=True,
                )

        partner = self.env["res.partner"].sudo().search([("vat", "=", fiscal_id)], limit=1)
        if partner:
            return {
                "vat": fiscal_id,
                "name": partner.name,
                "comment": partner.comment or "Registro local Odoo.",
                "company_type": partner.company_type or ("company" if len(fiscal_id) == 9 else "person"),
                "is_company": bool(partner.is_company if partner.is_company is not None else len(fiscal_id) == 9),
            }
        return None

    def _get_l10n_do_dgii_payer_types_selection(self):
        return [
            ("taxpayer", "Contribuyente Fiscal"),
            ("non_payer", "No Contribuyente"),
            ("nonprofit", "Organizacion sin animo de lucro"),
            ("special", "Regimen Especial"),
            ("governmental", "Gubernamental"),
            ("foreigner", "Extranjero/a"),
            ("self", "Empresa del sistema"),
        ]

    def _get_l10n_do_expense_type(self):
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

    @api.depends("vat", "country_id", "name")
    def _compute_l10n_do_dgii_payer_type(self):
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
                partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

    def _inverse_l10n_do_dgii_tax_payer_type(self):
        for partner in self:
            partner.l10n_do_dgii_tax_payer_type = partner.l10n_do_dgii_tax_payer_type

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for reg in res.filtered(lambda p: not p.property_account_position_id):
            reg._set_position_fiscal()
        return res

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
                            "getupsoft_l10n_do_accounting.final_consumer", raise_if_not_found=False
                        ).id if self.env.ref("getupsoft_l10n_do_accounting.final_consumer", raise_if_not_found=False) else False
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

    @api.model
    def validate_rnc_cedula(self, fiscal_id):
        fiscal_id = normalize_fiscal_id(fiscal_id)
        invalid_fiscal_id_message = (
            500,
            u"RNC/Cedula invalido",
            u"El numero de RNC/Cedula no es valido.",
        )
        if not fiscal_id:
            return 0, invalid_fiscal_id_message
        try:
            dgii_data = self._lookup_official_fiscal_id(fiscal_id)
            if not dgii_data:
                dgii_data = self._lookup_local_fiscal_id(fiscal_id)
            if dgii_data:
                dgii_data.update(
                    {
                        "vat": dgii_data["vat"],
                        "name": dgii_data["name"],
                        "comment": dgii_data.get("comment", "Registro local."),
                        "company_type": dgii_data.get(
                            "company_type",
                            "company" if len(fiscal_id) == 9 else "person",
                        ),
                        "is_company": dgii_data.get(
                            "is_company",
                            len(fiscal_id) == 9,
                        ),
                    }
                )
                return 1, dgii_data
            return 0, invalid_fiscal_id_message
        except Exception as exc:
            _logger.error(exc)
            return 0, "Error de consulta DGII"
