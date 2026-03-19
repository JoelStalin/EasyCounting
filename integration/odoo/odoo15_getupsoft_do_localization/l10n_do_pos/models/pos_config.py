from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    def _default_payment_methods(self):
        # OVERWRITE
        pay_methods = super()._default_payment_methods()
        pay_methods |= self.env["pos.payment.method"].search(
            [
                ("is_nc_type", "=", True),
                ("company_id", "=", self.env.company.id),
            ]
        )
        return pay_methods

    def _default_do_partner(self):
        return self.env.ref(
            "l10n_do_pos.consumer_contact_default",
            raise_if_not_found=False,
        )

    l10n_do_default_partner_id = fields.Many2one(
        "res.partner", string="Default partner", default=_default_do_partner
    )
    l10n_latam_use_documents = fields.Boolean(
        related="invoice_journal_id.l10n_latam_use_documents",
    )
    l10n_latam_country_code = fields.Char(
        related="company_id.country_id.code",
        help="Technical field used to hide/show fields regarding the localization",
    )

    @api.constrains("company_id", "journal_id")
    def _check_company_journal(self):
        if self.filtered(
            lambda config: config.journal_id
            and config.journal_id.l10n_latam_use_documents
            and config.journal_id.company_id.country_id.code == "DO"
        ):
            raise ValidationError(
                _(
                    "You cannot set a Fiscal Journal as Sales Journal. "
                    "Please, select a non-fiscal journal."
                )
            )
        super(PosConfig, self)._check_company_journal()
