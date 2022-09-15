# -*- coding: utf-8 -*-
{
    "name": "maxcam vendedores",
    "summary": """
        personalizaciones para el pago de vendedores MaxCam""",
    "description": """
        Modulo personalizaciones especificas para Maxcam
    """,
    "author": "Antony H.",
    "company": "Binauraldev",
    "maintainer": "Antony H. / Binauraldev",
    "website": "https://www.binauraldev.com",
    "category": "Human Resources/Expenses",
    "version": "14.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": ["hr_expense", "account_accountant", "web"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/hr_expense_data.xml",
        "data/cron.xml",
        # 'views/commission_policy.xml',
        "views/account_move.xml",
        "views/hr_employee.xml",
        "views/res_partner.xml",
        "views/hr_expense.xml",
        "wizard/account_expense_wizard.xml",
        # 'views/stock_picking_batch.xml',
        # 'views/stock_picking.xml',
        "report/report_deliveryslip.xml",
        "report/report_picking_operations.xml",
        "report/report_commission_payment.xml",
        "views/hr_employee.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
    "images": ["static/description/icon.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
