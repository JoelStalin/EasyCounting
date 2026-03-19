from odoo import SUPERUSER_ID, api

from . import models


def _update_account_fiscal_position(env):
    if "account.fiscal.position.template" in env.registry:
        char_template = env.company.chart_template_id
    else:
        char_template = False

    if char_template:
        template_positions = env["account.fiscal.position.template"].search(
            [("chart_template_id", "=", char_template.id)]
        )
        for template_position in template_positions:
            if template_position.l10n_do_ncf_ids:
                template_xmlids = template_position.get_external_id()
                module, name = template_xmlids[template_position.id].split(".", 1)
                xml_id = "%s.%s_%s" % (module, env.company.id, name)

                position = env.ref(xml_id)

                position.write({"l10n_do_ncf_ids": template_position.l10n_do_ncf_ids})

    # Agregar los e-NCF a sus respectivo diarios.
    for journal in (
        env["account.journal"]
        .sudo()
        .search(
            [
                ("l10n_latam_use_documents", "=", True),
                ("type", "in", ("sale", "purchase")),
                ("company_id", "=", env.company.id),
            ]
        )
    ):
        journal._l10n_do_create_ncf_controles()


def _getupsoft_l10n_do_e_accounting_post_init(env_or_cr, registry=None):
    if hasattr(env_or_cr, "registry"):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    _update_account_fiscal_position(env)
