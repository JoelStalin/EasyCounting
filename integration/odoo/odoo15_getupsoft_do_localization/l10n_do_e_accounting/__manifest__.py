{
    "name": "Electronic Fiscal Localization (Dominican Republic)",
    "author": "Santos J. Marte M. <alejandro@neotec.do>, " "Neotec SRL",
    "website": "https://neotec.do/",
    "version": "1.0.0",
    "category": "Localization",
    "license": "LGPL-3",
    "depends": ["l10n_do_accounting"],
    "data": [
        "data/l10n_latam.document.type.csv",
        "data/account_fiscal_position_data.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
    "post_init_hook": "_l10n_do_e_accounting_post_init",
}
