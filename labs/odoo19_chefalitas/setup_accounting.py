import sys

def setup_full_accounting(env):
    try:
        company = env.user.company_id
        
        print(">> 1. Verificando Paquete Contable (Chart of Accounts)...")
        # La localización dominicana usa 'do' como sufijo para el chart template
        # En Odoo 16+ el chart template model desapareció y se usa l10n_modules
        if not company.chart_template:
            # Intento instalar la plantilla por defecto si existe
            env['account.chart.template'].try_loading('do', company)
            print(">> Plantilla contable 'do' cargada.")
        
        print(">> 2. Verificando Diarios Contables...")
        sales_journal = env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not sales_journal:
            print(">> Creando Diario de Ventas por defecto...")
            # Necesitamos una cuenta de ingresos
            income_account = env['account.account'].search([
                ('account_type', '=', 'income'), 
                ('company_id', '=', company.id)
            ], limit=1)
            
            sales_journal = env['account.journal'].create({
                'name': 'Ventas Locales',
                'code': 'VEN',
                'type': 'sale',
                'company_id': company.id,
                'default_account_id': income_account.id if income_account else False,
                'l10n_latam_use_documents': True,
            })
        else:
            sales_journal.write({'l10n_latam_use_documents': True})
            print(">> Diario de Ventas actualizado para usar documentos LATAM.")
            
        print(">> 3. Actualizando Datos de Compañía L10n DO...")
        do_country = env.ref('base.do', raise_if_not_found=False)
        company.write({
            'vat': '130862346',
            'country_id': do_country.id if do_country else False,
            'street': 'Av. Winston Churchill',
            'city': 'Santo Domingo',
        })
        if hasattr(company, 'l10n_do_ecf_issuer'):
            company.write({'l10n_do_ecf_issuer': True})

        print(">> 4. Verificando Cliente VIP...")
        ident_type_rnc = env['l10n_latam.identification.type'].search([('name', '=', 'RNC')], limit=1)
        customer = env['res.partner'].search([('vat', '=', '101000000')], limit=1)
        if not customer:
            customer = env['res.partner'].create({
                'name': 'Super Cliente Corporativo (B2B)',
                'vat': '101000000',
                'country_id': do_country.id if do_country else False,
                'customer_rank': 1,
                'l10n_latam_identification_type_id': ident_type_rnc.id if ident_type_rnc else False
            })
            
        env.cr.commit()
        print(">> Parametrización Contable Full Finalizada. Odoo listo para facturar.")

    except Exception as e:
        print(">> Error critico configurando contabilidad:", str(e))

if __name__ == "__main__":
    setup_full_accounting(env)
