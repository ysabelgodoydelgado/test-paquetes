# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderMaxcamPurchase(models.Model):
	_inherit = 'purchase.order'

	confirmed_update_cost = fields.Boolean(string='Actualizar Costos',default=False)
	wizard_confirm = fields.Boolean(string='Confirmado')

	def button_cancel(self):
		for order in self:
			for inv in order.invoice_ids:
				if inv and inv.state not in ('cancel', 'draft'):
					raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

		self.write({'state': 'cancel','wizard_confirm':False,'confirmed_update_cost':False})

	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent']:
				continue

			if not order.wizard_confirm:
				return {
					'name': 'Advertencia',
					'view_type': 'form',
					'view_mode': 'form',
					'view_id': self.env.ref('maxcam_purchase.wizard_message_maxcam_update_cost').id,
					'res_model': 'wizard.message.maxcam.update.cost',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'context': {
						'default_purchase_id': self.id,
						'default_name_modal_purchase_partial': '¿Quiere actualizar el costo de los productos?'
					},
				}
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step'\
					or (order.company_id.po_double_validation == 'two_step'\
						and order.amount_total < self.env.company.currency_id._convert(
							order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
					or order.user_has_groups('purchase.group_purchase_manager'):
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
			if order.partner_id not in order.message_partner_ids:
				order.message_subscribe([order.partner_id.id])

			if order.confirmed_update_cost:
				for line in order.order_line:
					if line.product_id and line.price_unit:
						line.product_id.write({'standard_price':line.price_unit})
		return True

class PurchaseOrderLineMaxcamm(models.Model):
	_inherit = 'purchase.order.line'

	alternate_code = fields.Char(related='product_id.alternate_code')
	
	@api.onchange('product_qty', 'product_uom')
	def _onchange_quantity(self):
		res = super(PurchaseOrderLineMaxcamm, self)._onchange_quantity()
		if not self.product_id:
			return
		product_id = self.product_id.id
		params = {'order_id': self.order_id}
		seller = self.product_id._select_seller(
			partner_id=self.partner_id,
			quantity=self.product_qty,
			date=self.order_id.date_order and self.order_id.date_order.date(),
			uom_id=self.product_uom,
			params=params)
		identifier = 'product.product,' + str(product_id)
		result = self.env['ir.property'].search([('res_id', '=', identifier)])
		self.price_unit = result.value_float
		product_ctx = {'seller_id': seller.id, 'lang': get_lang(self.env, self.partner_id.lang).code}
		self.name = self._get_product_purchase_description(self.product_id.with_context(product_ctx))
		return res
	
	def action_open_wizard_solds(self, id):
		
		return {'name': _('Vendidos'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'target': 'new',
				'res_model': 'sale.report',
				'view_id': self.env.ref('sale.view_order_product_pivot').id,
				'type': 'ir.actions.act_window',
				'context': {"default_product_id": id, "search_default_product_id": id, 'pivot_measures': ['product_uom_qty', "qty_invoiced"]},
			}
	
	@api.model
	def get_id_wizard_solds(self):
		return {
			'view_id': self.env.ref('sale.view_order_product_pivot').id
		}