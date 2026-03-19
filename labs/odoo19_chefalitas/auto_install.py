# Script para instalar módulos en Odoo de forma limpia sin colisión de puertos
import sys

def force_install_dependencies(env):
    try:
        # Modulos requeridos para la correcta operación DO
        required_modules = [
            'account_accountant',             # Enterprise base
            'l10n_do',                        # Core DO localization
            'getupsoft_l10n_do_accounting',   # Getupsoft overrides
            'getupsoft_l10n_do_e_accounting'  # Getupsoft ECF
        ]
        
        IRModule = env['ir.module.module']
        
        # Odoo requiere a veces actualizar la lista primero si el volumen en Docker se montó *después* de iniciar
        print(">> Actualizando lista de Addons en la BD (Update Apps List)...")
        IRModule.update_list()
        
        # Buscar modulos
        modules = IRModule.search([('name', 'in', required_modules)])
        found_names = modules.mapped('name')
        print(f">> Módulos encontrados en el filesystem: {found_names}")
        
        for mod in modules:
            if mod.state != 'installed':
                print(f">> Instalando {mod.name} de forma síncrona...")
                mod.button_immediate_install()
        
        print(">> Ejecución de instalación finalizada.")
        env.cr.commit()

    except Exception as e:
        print(">> Error instalando módulos:", str(e))

if __name__ == "__main__":
    force_install_dependencies(env)
