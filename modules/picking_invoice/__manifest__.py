# -*- coding: utf-8 -*-
{
    'name': "picking invoice",

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
    'category': 'Accounting/Warehouse',
    'version': '14.0.1.0.0',
    'depends': ['sale_stock', 'stock_picking_batch'],

    # always loaded
    'data': [
        #lo agrega el modulo comprado
        'views/account_move.xml', 
        'views/stock_picking.xml',
        'views/stock_picking_batch.xml',
        'report/report_picking_batch.xml',
    ],
    # only loaded in demonstration mode
    # 
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
