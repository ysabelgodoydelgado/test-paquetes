# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLineMaxCamInherit(models.Model):
    _inherit = 'sale.order.line'

    brand_id = fields.Many2one('product.brand', related="product_id.brand_id", string='Product brands',
                               help="field related to product and brands")

    available_qty = fields.Float(string="Disponible", related='product_id.available_qty')
    free_qty = fields.Float(string="Sin reserva", related='product_id.free_qty')
