from odoo import SUPERUSER_ID, api

from . import models, wizard, hooks


def _update_account_fiscal_position(env):
    if "account.fiscal.position.template" not in env.registry:
        return

    char_template = env.company.chart_template_id
    if char_template:
        template_positions = env["account.fiscal.position.template"].search(
            [("chart_template_id", "=", char_template.id)]
        )
        for template_position in template_positions:
            if template_position.l10n_do_ncf_ids:
                template_xmlids = template_position.get_external_id()
                module, name = template_xmlids[template_position.id].split(".", 1)
                xml_id = "%s.%s_%s" % (module, env.company.id, name)

                try:
                    position = env.ref(xml_id)
                except ValueError:
                    vals = char_template._get_fp_vals(env.company, template_position)
                    char_template.create_record_with_xmlid(
                        env.company, template_position, "account.fiscal.position", vals
                    )
                    position = env.ref(xml_id)

                position.write({"l10n_do_ncf_ids": template_position.l10n_do_ncf_ids})


def _getupsoft_l10n_do_accounting_post_init(env_or_cr, registry=None):
    if hasattr(env_or_cr, "registry"):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    _update_account_fiscal_position(env)
    hooks.auto_configure_l10n_do_base(env)
