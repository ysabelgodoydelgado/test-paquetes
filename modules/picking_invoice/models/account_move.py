# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMovePicking(models.Model):
    _inherit = 'account.move'

    picking_ids = fields.Many2many(comodel_name="stock.picking", string="Related Pickings", store=True,
                                   help="Related pickings(only when the invoice has been generated from a sale order).")
