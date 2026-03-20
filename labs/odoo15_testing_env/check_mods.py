import sys
def check(env):
    mods = env['ir.module.module'].search([('name', 'in', ['account', 'sale_management', 'l10n_do_accounting'])])
    for m in mods:
        print(f"MODULE: {m.name} | STATE: {m.state}")
check(env)
