import logging

_logger = logging.getLogger(__name__)

def auto_configure_l10n_do_base(env):
    """
    Hook automatically executed upon installing/updating the getupsoft_l10n_do_accounting module.
    It provisions the required structural parameters for the Dominican Localization
    WITHOUT burning specific client/company data (like RNC or Addresses) into the code.
    """
    try:
        _logger.info("Initializing base Dominican localization parameters...")
        
        # 1. Update Core Journals to support LATAM Documents
        sale_journals = env['account.journal'].search([('type', '=', 'sale')])
        if sale_journals:
            sale_journals.write({'l10n_latam_use_documents': True})
            _logger.info(f"Updated {len(sale_journals)} sales journals to use LATAM documents.")

        purchase_journals = env['account.journal'].search([('type', '=', 'purchase')])
        if purchase_journals:
            purchase_journals.write({'l10n_latam_use_documents': True})
        
        # 2. Ensure RNC Identification Type Exists globally
        do_country = env.ref('base.do', raise_if_not_found=False)
        ident_type_rnc = env['l10n_latam.identification.type'].search([('name', '=', 'RNC')], limit=1)
        if not ident_type_rnc and do_country:
            env['l10n_latam.identification.type'].create({
                'name': 'RNC',
                'is_vat': True,
                'country_id': do_country.id,
            })
            _logger.info("Created missing RNC Identification Type.")

        _logger.info("Successfully applied automatic base parameters for getupsoft_l10n_do_localization.")

    except Exception as e:
        _logger.error(f"Error during auto_configure_l10n_do_base: {e}")
