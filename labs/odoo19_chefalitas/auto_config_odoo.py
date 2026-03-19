# Script a inyectar en Odoo Shell para parametrizar la BD a nivel fiscal
import sys

def init_l10n_do(env):
    try:
        do_country = env.ref('base.do', raise_if_not_found=False)
        if not do_country:
            do_country = env['res.country'].search([('code', '=', 'DO')], limit=1)
            
        company = env.user.company_id
        company.write({
            'vat': '130862346',
            'country_id': do_country.id if do_country else False,
            'street': 'Torre Sonora Piso 4',
            'city': 'Santo Domingo',
        })
        
        # En la version 19 la configuracion 'l10n_do_ecf_issuer' vive en la compañía o en res.config.settings
        if hasattr(company, 'l10n_do_ecf_issuer'):
            company.write({'l10n_do_ecf_issuer': True})
            
        # Preparación de Diarios para soportar Tipos de Comprobantes 31, 32...
        journals = env['account.journal'].search([('type', '=', 'sale')])
        for j in journals:
            if hasattr(j, 'l10n_latam_use_documents'):
                j.write({'l10n_latam_use_documents': True})

        # Identificación de Empresa
        ident_type_rnc = env['l10n_latam.identification.type'].search([('name', '=', 'RNC')], limit=1)
        if not ident_type_rnc and do_country:
            ident_type_rnc = env['l10n_latam.identification.type'].create({
                'name': 'RNC',
                'is_vat': True,
                'country_id': do_country.id,
                'l10n_do_l10n_latam_identification_type': 'rnc'
            })
            
        # Parametrización de Cliente VIP 
        customer = env['res.partner'].search([('vat', '=', '101000000')], limit=1)
        if not customer:
            customer = env['res.partner'].create({
                'name': 'Super Cliente Corporativo (B2B)',
                'vat': '101000000',
                'country_id': do_country.id if do_country else False,
                'customer_rank': 1
            })
            if ident_type_rnc:
                customer.write({'l10n_latam_identification_type_id': ident_type_rnc.id})
                
        env.cr.commit()
        print(">> L10n DO Configurada Exitosamente en base de datos de Odoo")

    except Exception as e:
        print(">> Error al parametrizar l10n_do:", str(e))

if __name__ == "__main__":
    init_l10n_do(env)
