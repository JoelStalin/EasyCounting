from odoo import _, api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_l10n_do_payment_form(self):
        """Return the list of payment forms allowed by DGII."""
        return [
            ("cash", _("Cash")),
            ("bank", _("Check / Transfer")),
            ("card", _("Credit Card")),
            ("credit", _("Credit")),
            ("swap", _("Swap")),
            ("bond", _("Bonds or Gift Certificate")),
            ("others", _("Other Sale Type")),
        ]

    l10n_do_payment_form = fields.Selection(
        selection="_get_l10n_do_payment_form",
        string="Payment Form",
    )
    l10n_do_ncf_control_manager_ids = fields.One2many(
        "ncf.control.manager",
        "journal_id",
        string="NCFs",
        copy=False,
    )

    def _l10n_do_create_ncf_controles(self):
        self.ensure_one()

        if self.company_id.country_id != self.env.ref("base.do"):
            return True
        if not self.l10n_latam_use_documents:
            return False
        if self.type not in ("purchase", "sale"):
            return False

        latam_documents = self._get_latam_documents(
            self.type, self.l10n_do_ncf_control_manager_ids
        )
        if latam_documents:
            self.env["ncf.control.manager"].create(
                [
                    {"journal_id": self.id, "l10n_latam_document_type_id": line.id}
                    for line in latam_documents
                ]
            )

    def _get_latam_documents(self, journal_type, old_controlers=None):
        domain = [("country_id.code", "=", "DO")]
        if journal_type == "sale":
            internal_types = ("debit_note", "credit_note")
            domain.extend(
                [
                    "|",
                    ("l10n_do_use_in", "in", ("sale", "both")),
                    ("internal_type", "in", internal_types),
                ]
            )
        else:
            domain.extend(
                [
                    "|",
                    ("l10n_do_use_in", "in", ("purchase", "both")),
                    ("l10n_do_auto_sequence", "=", True),
                ]
            )

        if old_controlers is not None:
            domain.append(
                (
                    "doc_code_prefix",
                    "not in",
                    old_controlers.mapped(
                        "l10n_latam_document_type_id.doc_code_prefix"
                    ),
                )
            )

        return self.env["l10n_latam.document.type"].search(domain)

    @api.model
    def create(self, values):
        if (
            self.env.company.country_id == self.env.ref("base.do")
            and values.get("l10n_latam_use_documents", False)
            and values.get("type", "") in ("sale", "purchase")
        ):
            latam_documents = self._get_latam_documents(values["type"])
            values.update(
                {
                    "l10n_do_ncf_control_manager_ids": [
                        (0, 0, {"l10n_latam_document_type_id": line.id})
                        for line in latam_documents
                    ]
                }
            )

        return super().create(values)

    def write(self, values):
        to_check = {"type", "l10n_latam_use_documents"}
        res = super().write(values)
        if to_check.intersection(set(values.keys())):
            for rec in self:
                rec._l10n_do_create_ncf_controles()
        return res
