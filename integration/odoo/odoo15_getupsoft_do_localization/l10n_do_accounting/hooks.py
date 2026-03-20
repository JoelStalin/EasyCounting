# hooks.py
import logging

_logger = logging.getLogger(__name__)

def auto_configure_l10n_do_base(cr, registry):
    """
    Hook post_init para parametrizar de manera automática el entorno de Odoo 15
    al instalar o actualizar el submódulo l10n_do_accounting, garantizando pruebas confiables.
    Basado en la configuración productiva (neo_do_localization).
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    _logger.info("Iniciando inyección de parámetros productivos para l10n_do_accounting (Odoo 15)...")

    # 1. Configurar Diarios de Venta para LATAM
    journals = env['account.journal'].search([('type', '=', 'sale')])
    if hasattr(env['account.journal'], 'l10n_latam_use_documents'):
        for journal in journals:
            journal.write({'l10n_latam_use_documents': True})
            _logger.info("Diario '%s' parametrizado para usar Documentos LATAM.", journal.name)

    # 2. Asegurar Tipos de Identificación base de DGII 
    rnc_type = env['l10n_latam.identification.type'].search([('name', '=', 'RNC')], limit=1)
    if not rnc_type:
        env['l10n_latam.identification.type'].create({
            'name': 'RNC',
            'description': 'Registro Nacional del Contribuyente',
            'country_id': env.ref('base.do', raise_if_not_found=False).id if env.ref('base.do', raise_if_not_found=False) else False,
            'is_vat': True,
            'sequence': 10,
        })
        _logger.info("Tipo de Identidad 'RNC' creado automáticamente.")

    # 3. Configurar Tipo de Gasto PREDETERMINADO (02-Gastos por trabajos) en res.company para nuevos partners
    company = env.company
    if hasattr(company, 'l10n_do_expense_type'):
        company.write({'l10n_do_expense_type': '02'})

    _logger.info("Post init hook (auto_configure_l10n_do_base) ejecutado satisfactoriamente.")
