# -*- coding: utf-8 -*-
{
    'name': "maxcam pagos",

    'summary': """
        Campos y funciones para pagos Maxcam""",

    'description': """
        personalizaciones gestión de pagos MaxCam
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Approvals/Accounting',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['mail','account','account_payment_batch_process','maxcam_seller'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/hr_employee_inh.xml',
        'views/lists.xml',
        'views/retention_register.xml',
        # 'views/templates.xml',
        'views/account.xml',
        'views/res_config_settings_inh.xml',
        'data/email_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
