# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class InvoiceLineBrand(models.Model):
    _inherit = 'account.invoice.report'
    _description = 'Herencia de estadisticas de lineas de venta'

    brand_id = fields.Many2one('product.brand', related="product_id.brand_id", string='Marca',
                               help="field related to product and brands")    

    # def _select(self):
    #     return super(AccountInvoiceReport, self)._select() + ", sub.team_id as team_id"

    # def _sub_select(self):
    #     return super(AccountInvoiceReport, self)._sub_select() + ", ai.team_id as team_id"

    # def _group_by(self):
    #     return super(AccountInvoiceReport, self)._group_by() + ", ai.team_id"