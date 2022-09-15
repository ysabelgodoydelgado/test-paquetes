# -*- coding: utf-8 -*-
{
    "name": "Maxcam Inventario",
    "summary": """
        personalizaciones inventario MaxCam """,
    "description": """
        Modulo personalizaciones especificas para Maxcam
    """,
    "author": "Antony H.",
    "company": "Binauraldev",
    "maintainer": "Antony H. / Binauraldev",
    "website": "https://www.binauraldev.com",
    "category": "Warehouse",
    "version": "14.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": ["stock", "maxcam_sale_management", "stock_picking_batch", "maxcam_account"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/paperformat.xml",
        "data/report_zebra.xml",
        "data/cron.xml",
        "views/assets.xml",
        "views/product_brand.xml",
        "views/product_template.xml",
        "views/sale_order_line.xml",
        "views/stock_picking_batch.xml",
        "views/res_partner.xml",
        "views/account_move.xml",
        "views/stock_picking_alter_location_views.xml",
        "views/stock_picking_alter_location_line_views.xml",
        "views/stock_picking.xml",
        "report/report_picking_batch.xml",
        "report/report_simple_label_inherit.xml",
        "report/report_picking_operations.xml",
        "report/report_deliveryslip.xml",
        "report/report_pricelist_page.xml",
        "report/report_picking_zebra.xml",
        "views/action_menu_lot.xml",
        "views/stock_warehouse.xml",
    ],
    "qweb": ["static/src/xml/pricelist_report.xml"],
    # only loaded in demonstration mode
    "demo": [],
    "images": ["static/description/icon.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
