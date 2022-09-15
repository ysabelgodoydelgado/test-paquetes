# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Vicent Cubells
# Copyright 2020 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Line Report",
    "summary": "New view to manage invoice lines information",
    "version": "14.0.1.0.0",
    "category": "Account",
    "website": "https://github.com/OCA/account-invoice-reporting",
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base","account","maxcam_stock","stock"],
    "data": [
        "report/account_invoice_report_view.xml"     
        # "report/invoice_lines_brand_view.xml"     
        ],
    "installable": True,
}
