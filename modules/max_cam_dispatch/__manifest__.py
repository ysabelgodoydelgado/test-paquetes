# -*- coding: utf-8 -*-
{
    'name': "Maxcam despacho",

    'summary': """
        Campos y funciones para el despacho Maxcam""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Raiver F.",
    'company': 'Binauraldev',
    'maintainer': 'Raiver F. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Accounting/Warehouse',
    'version': '14.0.1.0.0',
    'depends': ['stock_picking_batch','picking_invoice','hr','fleet', 'maxcam_account','maxcam_seller'],

    # always loaded
    'data': [
        'views/stock_picking_batch_inh.xml',
        'data/jobs.xml',
        'data/formato_papel_deliveryship.xml',
        'views/stock_picking_inh.xml',
        'views/account_move.xml',
        'report/report_picking_batch.xml',
        'report/report_picking_operations.xml',
        'report/report_deliveryslip.xml',
        'report/invoice_free_form.xml',
        "report/report_deliveryslip_view.xml",
        "report/report_depatch.xml",
        "report/report.xml",
        'views/product_inh.xml',
        'views/stock_picking_batch.xml',
        'views/stock_picking.xml',
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
