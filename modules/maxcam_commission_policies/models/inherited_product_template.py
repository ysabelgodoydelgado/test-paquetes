import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    commission_policy_id = fields.Many2one('commission.policy', string="Comisión")
    commission_policy_image_id = fields.Many2one('commission.policy.image', string="Imagen de Comisión")
