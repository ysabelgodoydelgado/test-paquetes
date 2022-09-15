# -*- coding: utf-8 -*-
{
    'name': "Binaural Versionado de Aplicaciones Moviles",

    'summary': """
        Módulo de versionado de aplicaciones""",

    'description': """
        Módulo de versionado de aplicaciones
    """,

    'author': "Binauraldev",
    'company': 'Binauraldev',
    'maintainer': 'Binauraldev / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Accounting',
    'version': '14.0.1.0.0',
    'depends': ['account'],

    # always loaded
    'data': [
        'views/configurate_ver.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
