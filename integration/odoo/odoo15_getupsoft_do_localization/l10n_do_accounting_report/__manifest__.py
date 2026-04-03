{
    "name": "DO Accounting Report",
    "author": "Santos J. Marte M. <alejandro@neotec.do> ; Neotec SRL",
    "website": "https://neotec.do/",
    "version": "15.0.1.0.0",
    "category": "Accounting",
    "depends": ["base", "l10n_do_accounting"],
    "data": [
        "data/invoice_service_type_detail_data.xml",
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/account_tax_view.xml",
        "views/account_account_view.xml",
        "views/account_move_view.xml",
        "views/dgii_report_view.xml",
        "wizard/dgii_report_regenerate_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_do_accounting_report/static/src/css/style.css",
            "l10n_do_accounting_report/static/src/js/widget.js",
        ]
    },
    "license": "LGPL-3",
    "external_dependencies": {"python": ["pycountry"]},
    "installable": True,
    "auto_install": True,
}
