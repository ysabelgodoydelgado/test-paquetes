# -*- coding: utf-8 -*-
{
    'name': "Maxcam Depósito de Pagos",

    'summary': """
        personalizaciones para depósito de los pagos MaxCam""",

    'description': """
        Modulo personalizaciones especificas para Maxcam
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Accounting',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'maxcam_seller','maxcam_payments'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/deposit_payments.xml',
        'views/res_config_settings_inh.xml',
        'views/views.xml',
        # 'views/res_partner.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
