import sys
def install(env):
    mods = env['ir.module.module'].search([('name', 'in', ['account', 'l10n_do_accounting'])])
    for m in mods:
        if m.state != 'installed':
            print(f"Installing {m.name}...")
            m.button_immediate_install()
    env.cr.commit()
    print("Done installing!")
install(env)
