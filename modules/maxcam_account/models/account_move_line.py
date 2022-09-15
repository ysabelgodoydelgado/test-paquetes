from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMoveLineMaxcam(models.Model):
    _inherit = 'account.move.line'

    @api.constrains('price_unit')
    def _constrains_standard_price(self):
        for record in self:
            if record.move_id.move_type == 'out_invoice' and record.product_id:
                if record.price_unit < record.product_id.standard_price:
                    raise UserError(_("Los precios de venta no pueden ser menor que el costo de venta"))