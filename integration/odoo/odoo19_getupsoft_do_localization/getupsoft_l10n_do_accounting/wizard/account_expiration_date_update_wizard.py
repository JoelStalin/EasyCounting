import psycopg2

from odoo import models, fields, _, api, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.orm.registry import Registry


class ExpirationDateUpdateWizard(models.TransientModel):
    _name = "account.expiration.date.update_wizard"
    _description = "Account Expiration Date Update Wizard"

    debug_logging = True
    document_type_id = fields.Many2one(
        "l10n_latam.document.type",
        "Document type",
        required=True,
    )
    l10n_do_ncf_max_number = fields.Integer(string="Max number")
    l10n_do_ncf_expiration_date = fields.Date(string="New Expiration date", required=True)

    def update_expiration_date(self):
        self.ensure_one()
        old1 = self.document_type_id.l10n_do_ncf_expiration_date
        old2 = self.document_type_id.l10n_do_ncf_max_number
        if ( self.l10n_do_ncf_expiration_date < old1 or self.l10n_do_ncf_max_number < old2):
            raise UserError(_("You must set a date later than the current one"))

        self.document_type_id.sudo().write({
            "l10n_do_ncf_max_number": self.l10n_do_ncf_max_number,
            "l10n_do_ncf_expiration_date": self.l10n_do_ncf_expiration_date,
        })
        # estos valores son sensible por tanto usamos el ir.loggin para guardar un registro
        # de quien modifo y los valores de los campos
        self.log_xml(
            f'updated by={self.env.user.id} ;'
            f' old date={old1} , old max={old2} ;'
            f' new date={self.l10n_do_ncf_expiration_date} , new max={self.l10n_do_ncf_max_number}',
            'update_expiration_date',
        )

    def log_xml(self, xml_string, func):
        self.ensure_one()

        if self.debug_logging:
            self.env.flush_all()
            db_name = self.env.cr.dbname

            # Use a new cursor to avoid rollback that could be caused by an upper method
            try:
                db_registry = Registry(db_name)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    IrLogging = env['ir.logging']
                    IrLogging.sudo().create({
                        'name': self._name,
                        'type': 'server',
                        'dbname': db_name,
                        'level': 'DEBUG',
                        'message': xml_string,
                        'path': str(__name__),
                        'func': func,
                        'line': 1})
            except psycopg2.Error:
                pass

    @api.onchange('document_type_id')
    def _set_parameters(self):
        if self.document_type_id:
            self.update({
                "l10n_do_ncf_max_number": self.document_type_id.l10n_do_ncf_max_number,
                "l10n_do_ncf_expiration_date": self.document_type_id.l10n_do_ncf_expiration_date,
            })
