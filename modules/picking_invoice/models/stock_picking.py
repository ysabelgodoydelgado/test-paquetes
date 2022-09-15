# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockPickingAccountMove(models.Model):
    _inherit = 'stock.picking'

    invoice_ids = fields.Many2many(comodel_name="account.move", string="Invoices", readonly=False)
