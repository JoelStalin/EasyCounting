{
    "name": "GetUpSoft Fiscal Localization (Dominican Republic)",
    "author": "GetUpSoft <info@getupsoft.com.do>",
    "website": "https://getupsoft.com.do/",
    "version": "19.0.1.0.0",
    "category": "Localization",
    "license": "LGPL-3",
    "depends": ["l10n_latam_invoice_document", "l10n_do", "web"],
    "data": [
        "data/l10n_latam.document.type.csv",
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "_getupsoft_l10n_do_accounting_post_init",
    "installable": True,
    "auto_install": False,
    "application": False,
}
