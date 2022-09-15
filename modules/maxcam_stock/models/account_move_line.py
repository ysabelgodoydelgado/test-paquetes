# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError,ValidationError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class MaxcamAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    brand_id = fields.Many2one('product.brand', related="product_id.brand_id", string='Product brands',
                               help="field related to product and brands")
