# -*- coding: utf-8 -*-
{
    'name': "Binaural Retenciones",

    'summary': """
        Modulo de retenciones""",

    'description': """
        Modulo de retenciones
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
        'security/ir.model.access.csv',
        'views/config.xml',
        'views/configurate_vat.xml',
        'views/res_country_state.xml',
        'views/res_partner_master.xml',
        'views/type_person.xml',
        'views/withholdings.xml',

    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
