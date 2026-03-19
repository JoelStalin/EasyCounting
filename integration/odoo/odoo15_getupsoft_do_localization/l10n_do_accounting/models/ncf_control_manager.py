import logging
from datetime import timedelta
import psycopg2
from odoo import SUPERUSER_ID, api, fields, models, registry, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

# TODO: esto deberia estar parametrizado ?
MAX_DAY = 3


class NcfControlManager(models.Model):
    _name = "ncf.control.manager"
    _inherit = ["mail.thread"]
    _description = "NCF Control Manager"
    _rec_name = "l10n_latam_document_type_id"

    debug_logging = True

    journal_id = fields.Many2one(
        "account.journal", "Journal", required=True, readonly=True
    )
    company_id = fields.Many2one(
        "res.company", related="journal_id.company_id", store=True
    )
    l10n_latam_document_type_id = fields.Many2one(
        "l10n_latam.document.type", "Document type", required=True, readonly=True
    )
    l10n_do_ncf_expiration_date = fields.Date(
        string="Expiration date",
        required=True,
        default=fields.Date.end_of(fields.Date.today(), "year"),
        tracking=True,
    )
    l10n_do_ncf_max_number = fields.Integer(
        string="Max number",
        required=True,
        default=1,
        tracking=True,
    )

    def write(self, vals):
        if "l10n_do_ncf_max_number" in vals:
            # estos valores son sensible por tanto usamos el ir.loggin para guardar un registro
            # de quien modifo y los valores de los campos
            self.log_xml(
                f"updated by={self.journal_id and self.env.user.id} ;"
                f" company id={self.env.company.id} ;"
                f" journa id={self.journal_id.id} ;"
                f" document type id={self.l10n_latam_document_type_id and self.l10n_latam_document_type_id.id} ;"
                f" old max={self.l10n_do_ncf_max_number} ;"
                f' new max={vals["l10n_do_ncf_max_number"]}',
                "update_ncf_max_number",
            )

        if "l10n_do_ncf_expiration_date" in vals:
            # estos valores son sensible por tanto usamos el ir.loggin para guardar un registro
            # de quien modifo y los valores de los campos
            self.log_xml(
                f"updated by={self.env.user.id} ;"
                f" company id={self.env.company.id} ;"
                f" journa id={self.journal_id and self.journal_id.id} ;"
                f" document type id={self.l10n_latam_document_type_id and self.l10n_latam_document_type_id.id} ;"
                f" old expiration_date={self.l10n_do_ncf_expiration_date} ;"
                f' new expiration_date={vals["l10n_do_ncf_expiration_date"]}',
                "update_ncf_expiration_date",
            )
        return super().write(vals)

    def log_xml(self, xml_string, func):
        self.ensure_one()

        if self.debug_logging:
            self.flush()
            db_name = self._cr.dbname

            # Use a new cursor to avoid rollback that could be caused by an upper method
            try:
                db_registry = registry(db_name)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    IrLogging = env["ir.logging"]
                    IrLogging.sudo().create(
                        {
                            "name": self._name,
                            "type": "server",
                            "dbname": db_name,
                            "level": "DEBUG",
                            "message": xml_string,
                            "path": str(__name__),
                            "func": func,
                            "line": 1,
                        }
                    )
            except psycopg2.Error:
                pass

    @api.model
    def _ncf_auto_verifier_expired(self):
        limit_day = fields.Date.context_today(self) + timedelta(days=MAX_DAY)
        ncfs = self.search([('l10n_do_ncf_expiration_date', '<=', limit_day)])
        self._send_email(ncfs)

    @api.model
    def _search_users_billing_administrator(self):
        group_id = self.env.ref('account.group_account_manager')
        if not group_id:
            return self.env['res.users']
        return self.env['res.users'].sudo().search([('groups_id', 'in', group_id.ids)])

    @api.model
    def _send_email(self, ncfs):
        for user in self._search_users_billing_administrator():
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                self._make_and_send_emal(user.email, ncfs)
            _logger.info("NCFs expired email sent for user <%s> to <%s>", user.login, user.email)

    @api.model
    def _make_and_send_emal(self, email, ncfs):
        if not email or not ncfs:
            return

        company = self.env.user.company_id
        render_context = {
            "company": company,
            "ncfs": ncfs,
            "max_day": MAX_DAY,
        }
        template = self.env.ref('l10n_do_accounting.email_template_ncf_expirate_report')
        mail_body = template._render(render_context, engine='ir.qweb', minimal_qcontext=True)
        mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)
        mail = self.env['mail.mail'].sudo().create(
            {
                'subject': f"{company.name}: NCFs pronto a vencer",
                'email_from': company.catchall_formatted or company.email_formatted,
                'author_id': self.env.user.partner_id.id,
                'email_to': email,
                'body_html': mail_body,
            })
        mail.send()
