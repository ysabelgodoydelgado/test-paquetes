# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_note = fields.Text('Nota de presupuesto', related='sale_id.note')

    def do_print_tag(self):
        data = {}
        return self.env.ref('maxcam_stock.action_report_picking_zebra_tag').report_action(self, data=data)

    def trigger_assign_of_confirmed_picking(self):
        confirmed_pickings = self.env["stock.picking"].search([('picking_type_id', '=', self.env.ref("stock.picking_type_out").id), ('state', '=', 'confirmed')])

        for confirmed_picking in confirmed_pickings:
            confirmed_picking.action_assign()