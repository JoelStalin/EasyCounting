{
    "name": "GetUpSoft Electronic Fiscal Localization (Dominican Republic)",
    "author": "GetUpSoft <info@getupsoft.com.do>",
    "website": "https://getupsoft.com.do/",
    "version": "19.0.1.0.0",
    "category": "Localization",
    "license": "LGPL-3",
    "depends": ["getupsoft_l10n_do_accounting"],
    "data": [
        "data/l10n_latam.document.type.csv",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "_getupsoft_l10n_do_e_accounting_post_init",
}
