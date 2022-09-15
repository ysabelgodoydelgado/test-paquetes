# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingMaxCam(models.Model):
    _inherit = 'stock.picking.batch'

    # state = fields.Selection(selection_add=[('delivered', "Delivered"), ('done',)],
    #                          ondelete={'delivered': 'set default'})

    dispatch_date = fields.Date(string="Dispatch date", help="Date that indicates the day of dispatch of everything")

    # def action_delivered(self):
    #     if self.dispatch_date:
    #         return self.write({'state': 'delivered'})
    #     else:
    #         raise UserError(_('Select a dispatch date.'))

    def action_done(self):
        self.ensure_one()
        if not self.dispatch_date:
            raise UserError(_('Select a dispatch date.'))
        res = super(StockPickingMaxCam, self).action_done()
        return res
