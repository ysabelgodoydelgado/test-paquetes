# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SellerExpense(models.Model):
    _inherit = "hr.expense"

    invoice_ids = fields.One2many('account.move', 'hr_expense_id', 'Invoices',
                                  help="invoices associated with the seller, paid or payable")
    paid_seller = fields.Boolean(default=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        seller_product = self.env.ref('maxcam_seller.product_product_sellers_payment').id
        if self.product_id.id and self.product_id.id == seller_product:
            self.paid_seller = True
        else:
            self.paid_seller = False

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        res = super(SellerExpense, self)._compute_state()
        for record in self:
            if record.state == 'done' and record.paid_seller and len(record.invoice_ids) > 0:
                record.invoice_ids.write({'paid_seller': 'paid'})
            elif record.state == 'refused' and record.paid_seller and len(record.invoice_ids) > 0:
                record.invoice_ids.write({'hr_expense_id': False})
        return res
