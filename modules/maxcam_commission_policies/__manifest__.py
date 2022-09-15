{
    'name': "Maxcam Politica de Comisiones",
    'summary':
        """
            Personalizacion para las Politicas de Comisiones de MaxCam
        """,
    'description':
        """ 
            Modulo para generar las politicas de comisiones y calcularla para los gatos en base a condiciones. 
        """,
    'author': "Jose Vizcya",
    'company': "Binauraldev",
    'license': 'AGPL-3',
    'maintainer': "Jose Vizcya / Binauraldev",
    'website': "https://www.binauraldev.com",
    'category': "Expense/Payroll",
    'version': "14.0.1.0.0",
    'depends': [
        'account',
        'maxcam_stock',
    ],
    'demo': [],
    'data': [
        "security/ir.model.access.csv",

        "data/cron.xml",

        "views/commission_policy_views.xml",
        "views/commission_policy_line_views.xml",
        "wizard/invoice_commission_summary_wizard_views.xml",
        "views/commission_policy_image_views.xml",
        "views/commission_policy_image_line_views.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
