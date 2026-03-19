# -*- coding: utf-8 -*-
{
    'name': "GetUpSoft RNC DGII Search",
    'summary': """
      Buscador de RNC en DGII
          """,
    'description': """
         Buscador de RNC en DGII adaptado por GetUpSoft para la suite
         `getupsoft_do_localization` usada como base de integracion con `dgii_encf`.
    """,
    'website': 'https://getupsoft.com.do/',
    'author': 'GetUpSoft <info@getupsoft.com.do>',
    'category': 'Localization',
    'version': '19.0.1.0.0',
    'depends': ['base', 'getupsoft_l10n_do_accounting'],
    'assets': {
        'web.assets_backend': [
            'getupsoft_l10n_do_rnc_search/static/src/js/dgii_autocomplete.js',
        ]
    },
    'data': [
        'data/ir_config_parameters.xml',
        'views/res_partner_views.xml',
    ],
    'auto_install': True,
    'installable': True,
    "license": "LGPL-3",
}
