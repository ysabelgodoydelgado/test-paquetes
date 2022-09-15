# -*- coding: utf-8 -*-
{
    'name': "Binaural stock",

    'summary': """
        asegurar que no se pueda vender un producto que no tiene disponibilidad""",

    'description': """
        Este modulo agrega un campo en configuracion para activar la validacion y no permitir vender un producto 
        que no tiene disponibilidad
    """,
    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Warehouse',
    'version': '14.0.1.0.0',
    'depends': ['stock'],

    # always loaded
    'data': [
        'views/res_config_settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
