# setup_country_currency_15.py
import sys

def setup_environment(env):
    try:
        print(">> Configurando Entorno Odoo 15 (País: RD, Moneda: DOP)...")
        company = env.company
        country_do = env.ref('base.do', raise_if_not_found=False)
        currency_dop = env.ref('base.DOP', raise_if_not_found=False)
        
        if country_do:
            company.write({'country_id': country_do.id})
            print(f">> País asignado a la compañía: {company.country_id.name}")
            
        if currency_dop:
            company.write({'currency_id': currency_dop.id})
            print(f">> Moneda asignada a la compañía: {company.currency_id.name}")
            
        env.cr.commit()
        print(">> Configuración exitosa.")
    except Exception as e:
        print(f">> Error en configuración Odoo 15: {e}")

if __name__ == "__main__":
    setup_environment(env)
