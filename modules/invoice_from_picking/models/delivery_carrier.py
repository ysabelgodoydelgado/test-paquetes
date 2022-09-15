# Part of AntonyH. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class ProviderGrid(models.Model):
    _inherit = 'delivery.carrier'

    def _get_price_available_inv(self, invoice, total_order=0):
        self.ensure_one()
        self = self.sudo()
        invoice = invoice.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in invoice.invoice_line_ids:
            total_delivery += line.price_subtotal
            qty = line.product_uom_id._compute_quantity(line.quantity, line.product_uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        # total = (invoice.amount_total or 0.0) - total_delivery
        total = total_delivery
        total_inv = invoice.currency_id._convert(total, invoice.company_id.currency_id, invoice.company_id,
                                             invoice.invoice_date or fields.Date.today())
        total = invoice.currency_id._convert(total_order, invoice.company_id.currency_id, invoice.company_id,
                                                   invoice.invoice_date or fields.Date.today())
        return self._get_price_from_picking_inv(total, weight, volume, quantity, total_inv)

    def _get_price_from_picking_inv(self, total, weight, volume, quantity, total_inv):
        price = 0.0
        criteria_found = False
        price_dict = {'price': total, 'volume': volume, 'weight': weight, 'wv': volume * weight, 'quantity': quantity}
        if self.free_over and total >= self.amount:
            return 0
        for line in self.price_rule_ids:
            test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
            if test:
                price = line.list_base_price + line.list_price * total_inv
                criteria_found = True
                break
        if not criteria_found:
            raise UserError(_("No price rule matching this order; delivery cost cannot be computed."))

        return price
