# -*- coding: utf-8 -*-
{
    'name': "maxcam compras",

    'summary': """
        personalizaciones gestión de compras MaxCam""",

    'description': """
        Modulo personalizaciones especificas para Maxcam
    """,

    'author': "Antony H.",
    'company': 'Binauraldev',
    'maintainer': 'Antony H. / Binauraldev',
    'website': "https://www.binauraldev.com",
    'category': 'Inventory/Purchase',
    'version': '14.0.1.0.0',
    'depends': ['purchase', 'maxcam_stock'],
    # always loaded
    'data': [
        'views/purchase_order.xml',
        'report/report_purchaseorder_document.xml',
        'report/report_purchasequotation_document.xml',
        'views/wizard.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/widget_sale.xml'],
    # only loaded in demonstration mode
    'demo': [],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
