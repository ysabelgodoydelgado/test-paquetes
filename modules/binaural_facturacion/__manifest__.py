# -*- coding: utf-8 -*-
{
    'name': "Binaural Facturacion",

    'summary': """
        Modulo de Facturacion""",

    'description': """
        Modulo de Facturacion
    """,

    'author': "Binauraldev",
    'company': 'Binauraldev',
    'maintainer': 'Binauraldev / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Accounting',
    'version': '14.0.1.0.0',
    'depends': ['account','sale','purchase'],

    # always loaded
    'data': [
        'views/exempt_taxed.xml',
        'views/invoice_inh.xml',
        'views/purchase_inh.xml',
        'views/report_purchase_order.xml',
        'views/report_sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
