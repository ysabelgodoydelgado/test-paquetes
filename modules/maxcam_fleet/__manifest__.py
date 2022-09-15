# -*- coding: utf-8 -*-
{
    'name': "Maxcam Flota",

    'summary': """
        personalizaciones para la flota de Vehiculos MaxCam""",

    'description': """
        Modulo personalizaciones especificas para Maxcam
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Human Resources/Fleet',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['fleet'],

    # always loaded
    'data': [
        'views/fleet_vehicle.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
