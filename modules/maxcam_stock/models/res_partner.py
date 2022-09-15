# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerBrand(models.Model):
    _inherit = 'res.partner'

    product_brand_ids = fields.One2many('product.brand', 'partner_id', string="Supplier brands",
                                        help="Vendor Related Brands")
