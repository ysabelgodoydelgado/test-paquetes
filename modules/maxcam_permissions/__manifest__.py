# -*- coding: utf-8 -*-
{
    'name': "Maxcam permisos",

    'summary': """
        personalizaciones permisos para MaxCam""",

    'description': """
        Modulo permisos especificos para Maxcam
    """,

    'author': "Binaural C.A",
    'company': 'Binauraldev',
    'maintainer': 'Binauraldev',
    'website': "https://www.binauraldev.com",
    'version': '14.0',
    'depends': ['base', 'sale', 'stock', "account", "max_cam_dispatch"],
    # always loaded, 
    'data': [
        #'security/ir.model.access.csv',
        'security/maxcam_permissions.xml',
        'views/maxcam_permission_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
