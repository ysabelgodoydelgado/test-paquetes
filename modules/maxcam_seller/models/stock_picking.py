
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MaxcamstockPickingSeller(models.Model):
    _inherit = 'stock.picking'

    seller_id = fields.Many2one('hr.employee', related='partner_id.seller_id', string='Vendedor', store=True)
