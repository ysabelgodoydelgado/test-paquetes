# -*- coding: utf-8 -*-
{
    'name': "maxcam Facturación",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Accounting/Accounting',
    'version': '14.0.1.0.0',
    'depends': ['account_accountant', 'binaural_facturacion'],

    # always loaded
    'data': [
        'data/formato_papel.xml',
        'report/report_invoice_document.xml',
        'views/account_move.xml',
        'views/configurate_qty_lines_by_invoice.xml',
        'views/account_payment_inh.xml',
        'report/invoice_free_form.xml',
        'views/wizard_confirmation.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
