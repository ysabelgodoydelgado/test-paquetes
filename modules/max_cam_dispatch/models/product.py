

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import operator as py_operator
from ast import literal_eval
from collections import defaultdict

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round


class ProductMaxCamInhAdd(models.Model):
    _inherit = "product.template"
    qty_on_hand_checked = fields.Float(
        'Cantidades chequeadas',
        digits='Product Unit of Measure',default=0.0)

    qty_available_after_check = fields.Float(
        'Quantity On Hand', compute='_compute_quantities_check', store=True,
        digits='Product Unit of Measure')
    

    @api.depends('qty_on_hand_checked')
    def _compute_quantities_check(self):
        for p in self:
            p.qty_available_after_check = p.qty_available - p.qty_on_hand_checked

    def button_dummy_check(self):
        # TDE FIXME: this button is very interesting
        return True
