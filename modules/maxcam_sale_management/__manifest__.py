# -*- coding: utf-8 -*-
{
    'name': "Maxcam gestión de ventas",

    'summary': """
        personalizaciones gestión de ventas MaxCam""",

    'description': """
        Modulo personalizaciones especificas para Maxcam
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Sales/Sales',
    'version': '14.0.1.0.0',
    'depends': ['sale_management', 'delivery'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
