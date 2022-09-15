# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class ResConfigSettingsInvoice(models.TransientModel):
	_inherit = 'res.config.settings'

	qty_max = fields.Integer(string='Cantidad Máxima', required=True, default=25)


	def set_values(self):
		super(ResConfigSettingsInvoice, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('qty_max', self.qty_max)

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsInvoice, self).get_values()
		res['qty_max'] = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		return res


class SaleAdvancePaymentInvInvoice(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def create_invoices(self):
		sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
		qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		for order in sale_orders:
			qty_lines = len(order.order_line)
		if qty_max and qty_max <= qty_lines:
			qty_invoice = qty_lines / qty_max
		else:
			qty_invoice = 1
		if (qty_invoice - int(qty_invoice)) > 0:
			qty_invoice = int(qty_invoice) + 1
		else:
			qty_invoice = int(qty_invoice)
		for i in range(0, qty_invoice):
			if self.advance_payment_method == 'delivered':
				sale_orders._create_invoices(final=self.deduct_down_payments)
			else:
				# Create deposit product if necessary
				if not self.product_id:
					vals = self._prepare_deposit_product()
					self.product_id = self.env['product.product'].create(vals)
					self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

				sale_line_obj = self.env['sale.order.line']
				for order in sale_orders:
					amount, name = self._get_advance_details(order)

					if self.product_id.invoice_policy != 'order':
						raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
					if self.product_id.type != 'service':
						raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
					taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
					tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
					analytic_tag_ids = []
					for line in order.order_line:
						analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

					so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
					so_line = sale_line_obj.create(so_line_values)
					self._create_invoice(order, so_line, amount)
		if self._context.get('open_invoices', False):
			return sale_orders.action_view_invoice()
		return {'type': 'ir.actions.act_window_close'}


class SaleOrderInvoice(models.Model):
	_inherit = 'sale.order'

	def _create_invoices(self, grouped=False, final=False,date=None):
		"""
		Create the invoice associated to the SO.
		:param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
						(partner_invoice_id, currency)
		:param final: if True, refunds will be generated if necessary
		:returns: list of created invoices
		"""

		#qty lines by invoices
		qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		qty_lines = len(self.order_line)

		#si qty_max es 0 asignar por defecto 5 para que siempre deje facturar y las pruebas no fallen
		if qty_max == 0:
			qty_max = 5

		if qty_max and qty_max <= qty_lines:
			qty_invoice = qty_lines / qty_max
		else:
			qty_invoice = 1
		if (qty_invoice - int(qty_invoice)) > 0:
			qty_invoice = int(qty_invoice) + 1
		else:
			qty_invoice = int(qty_invoice)
		for i in range(0, qty_invoice):
			if not self.env['account.move'].check_access_rights('create', False):
				try:
					self.check_access_rights('write')
					self.check_access_rule('write')
				except AccessError:
					return self.env['account.move']

			# 1) Create invoices.
			invoice_vals_list = []
			invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
			for order in self:
				order = order.with_company(order.company_id)
				current_section_vals = None
				down_payments = order.env['sale.order.line']

				invoice_vals = order._prepare_invoice()
				invoiceable_lines = order._get_invoiceable_lines(final)

				if not any(not line.display_type for line in invoiceable_lines):
					raise self._nothing_to_invoice_error()

				invoice_line_vals = []
				down_payment_section_added = False
				for line in invoiceable_lines:
					#qty lines
					#set default qty_max_i para que en caso de que sea 0 igual deje facturar
					qty_max_i = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
					if qty_max_i == 0:
						qty_max_i = 5

					if len(invoice_line_vals) < qty_max_i:
						if not down_payment_section_added and line.is_downpayment:
							# Create a dedicated section for the down payments
							# (put at the end of the invoiceable_lines)
							invoice_line_vals.append(
								(0, 0, order._prepare_down_payment_section_line(
									sequence=invoice_item_sequence,
								)),
							)
							dp_section = True
							invoice_item_sequence += 1
						invoice_line_vals.append(
							(0, 0, line._prepare_invoice_line(
								sequence=invoice_item_sequence,
							)),
						)
						invoice_item_sequence += 1

				invoice_vals['invoice_line_ids'] = invoice_line_vals
				invoice_vals_list.append(invoice_vals)

			if not invoice_vals_list:
				raise self._nothing_to_invoice_error()

			# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
			if not grouped:
				new_invoice_vals_list = []
				invoice_grouping_keys = self._get_invoice_grouping_keys()
				for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
					origins = set()
					payment_refs = set()
					refs = set()
					ref_invoice_vals = None
					for invoice_vals in invoices:
						if not ref_invoice_vals:
							ref_invoice_vals = invoice_vals
						else:
							ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
						origins.add(invoice_vals['invoice_origin'])
						payment_refs.add(invoice_vals['payment_reference'])
						refs.add(invoice_vals['ref'])
					ref_invoice_vals.update({
						'ref': ', '.join(refs)[:2000],
						'invoice_origin': ', '.join(origins),
						'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
					})
					new_invoice_vals_list.append(ref_invoice_vals)
				invoice_vals_list = new_invoice_vals_list

			# 3) Create invoices.

			# As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
			# in a single invoice. Example:
			# SO 1:
			# - Section A (sequence: 10)
			# - Product A (sequence: 11)
			# SO 2:
			# - Section B (sequence: 10)
			# - Product B (sequence: 11)
			#
			# If SO 1 & 2 are grouped in the same invoice, the result will be:
			# - Section A (sequence: 10)
			# - Section B (sequence: 10)
			# - Product A (sequence: 11)
			# - Product B (sequence: 11)
			#
			# Resequencing should be safe, however we resequence only if there are less invoices than
			# orders, meaning a grouping might have been done. This could also mean that only a part
			# of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
			if len(invoice_vals_list) < len(self):
				SaleOrderLine = self.env['sale.order.line']
				for invoice in invoice_vals_list:
					sequence = 1
					for line in invoice['invoice_line_ids']:
						line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
						sequence += 1

			# Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
			# sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
			moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

			# 4) Some moves might actually be refunds: convert them if the total amount is negative
			# We do this after the moves have been created since we need taxes, etc. to know if the total
			# is actually negative or not
			if final:
				moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
			for move in moves:
				move.message_post_with_view('mail.message_origin_link',
					values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
					subtype_id=self.env.ref('mail.mt_note').id
				)
			return moves


