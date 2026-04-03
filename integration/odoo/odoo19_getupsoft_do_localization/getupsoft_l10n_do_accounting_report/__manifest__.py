{
    "name": "GetUpSoft DO Accounting Report",
    "author": "GetUpSoft <info@getupsoft.com.do>",
    "website": "https://getupsoft.com.do/",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "depends": ["base", "getupsoft_l10n_do_accounting"],
    "data": [
        "data/invoice_service_type_detail_data.xml",
        "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
    "external_dependencies": {"python": ["pycountry"]},
    "installable": True,
    "auto_install": True,
}
