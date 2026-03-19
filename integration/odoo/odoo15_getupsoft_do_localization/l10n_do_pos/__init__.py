from . import models  # noqa: F401

from odoo import api, SUPERUSER_ID


def _update_account_fiscal_position(env):
    char_template = env.company.chart_template_id
    if char_template:
        template_positions = env['account.fiscal.position.template']\
            .search([('chart_template_id', '=', char_template.id)])
        for template_position in template_positions:
            template_xmlids = template_position.get_external_id()
            module, name = template_xmlids[template_position.id].split('.', 1)
            xml_id = "%s.%s_%s" % (module, env.company.id, name)

            try:
                position = env.ref(xml_id)
            except ValueError:
                vals = char_template._get_fp_vals(env.company, template_position)
                char_template.create_record_with_xmlid(
                    env.company,
                    template_position,
                    "account.fiscal.position",
                    vals,
                )
                position = env.ref(xml_id)

            position.write({"l10n_do_to_invoice": template_position.l10n_do_to_invoice})


def _l10n_do_pos_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _update_account_fiscal_position(env)
