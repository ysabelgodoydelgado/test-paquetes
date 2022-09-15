# -*- coding: utf-8 -*-
import logging
import string

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrderMaxCam(models.Model):
	_inherit = 'sale.order'

	state_seller = fields.Char(string="Status de pedido para vendedores", compute="_state_seller")

	can_send_to_admin = fields.Boolean(string='Enviar a administración', default=False)

	tax_id_maxcam = fields.Integer(string='Impuesto a aplicar')

	number_of_pages = fields.Integer(string="Numero de paginas", compute="_compute_number_of_pages", store=True)

	@api.depends("picking_ids")
	def _compute_number_of_pages(self):
		for order in self:
			order.number_of_pages = len(order.picking_ids)
			
	@api.depends('state', 'invoice_ids')
	def _state_seller(self):
		for record in self:
			if record.state in ["draft", "sent"]:
				state_seller = "Borrador"
			elif record.state == "cancel":
				state_seller = "Cancelado"
			elif len(record.invoice_ids) > 0:
				state_seller = "Factura"
			else:
				state_seller = "Pedido de venta"
			record.state_seller = state_seller

	@api.constrains('amount_total')
	def _onchange_limit_credit(self):
		for record in self:
			record.ensure_one()
			if record.state in ['draft', 'sent'] and record.partner_id.credit_limit > 0:
				due = record.partner_id.total_due + record.amount_total
				if due > record.partner_id.credit_limit:
					raise UserError(_("The client does not have a Credit Limit available"))
			else:
				record.payment_term_id = record.env.ref('account.account_payment_term_immediate')

	def action_confirm(self):
		exception = False
		product_ids = []
		for record in self:
			for line in record.order_line:
				if line.product_id.type == 'product':
					if line.product_uom_qty > line.product_id.free_qty:
						product_ids.append(line.product_id.name + " (" + str(int(line.product_id.free_qty)) + ")")
						exception = True

			if exception:
				raise ValidationError(_("los siguientes productos superan la existencia %s ") % product_ids)
			due = record.partner_id.total_due + record.amount_total
			if due > record.partner_id.credit_limit:
				raise UserError(_("The client does not have a Credit Limit available"))
		res = super(SaleOrderMaxCam, self).action_confirm()
		return res

	@api.onchange('order_line')
	def no_duplicate_product_id(self):
		product_ids = []
		for line in self.order_line:
			if line.product_id.id in product_ids:
				raise UserError(_("no puede agregar un producto que ya fué agregado"))
			else:
				product_ids.append(line.product_id.id)

	@api.constrains('order_line')
	def _constrains_product_id(self):
		product_ids = []
		for line in self.order_line:
			if line.product_id.id in product_ids:
				raise UserError(_("no puede agregar un producto que ya fué agregado"))
			else:
				product_ids.append(line.product_id.id)

	def sync_lines(self):
		lines_without_invoice_lines = self.env['sale.order.line'].sudo().search([('invoice_lines','=',False),('state','in',['sale','done'])])
		orders = []
		for l in lines_without_invoice_lines:
			if l.order_id.name not in orders:
				orders.append(l.order_id.name)
		_logger.info("Cantidad de ordenes con lineas sin factura y que si estan confirmadas aun no se si esten como origen de factura %s",len(orders))
		orders_sale = []
		for o in orders:
			invoices = []
			inv = self.env['account.move'].sudo().search([('invoice_origin','=',o)])

			if inv:
				for i in inv:
					invoices.append(i.id)
			if len(invoices)>0:
				orders_sale.append({'order':o,'invoices':invoices})
		
		_logger.info("este es el resultado de las ordenes que no tienen lineas de factura asociada, pero si son origen de facturas %s",orders_sale)
		_logger.info("este es el resultado de las ordenes que no tienen lineas de factura asociada, pero si son origen de facturas %s",len(orders_sale))
		for orden in orders_sale:
			orden_obj = self.env['sale.order'].sudo().search([('name','=',orden.get("order",False))],limit=1)
			if orden_obj:
				for factura in orden.get('invoices',[]):
					factura_obj = self.env['account.move'].sudo().browse(int(factura))
					if factura_obj:
						for linea_factura in factura_obj.invoice_line_ids:
							for linea_pedido in orden_obj.order_line:
								if linea_factura.product_id.id == linea_pedido.product_id.id:
									#_logger.info("las lineas coinciden (al menos el producto es el mismo)")
									linea_factura.write({'sale_line_ids': [(4, linea_pedido.id)]})
									linea_pedido.write({'invoice_lines':[(4, linea_factura.id)]})


class SaleOrderLineMaxCam(models.Model):
	_inherit = 'sale.order.line'

	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		"""
		Launch procurement group run method with required/custom fields genrated by a
		sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
		depending on the sale order line product rule.
		"""
		_logger.warning("DISPARO ACTION LAUNCH RULE")
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		procurements = []
		output = []
		cont = 0
		cont_all = 0
		lista_items = []
		qty_lines = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		if not qty_lines:
			qty_lines = 15
		for item in self:
			if cont < qty_lines:
				lista_items.append(item)
				cont += 1
				cont_all += 1

			if cont == qty_lines or len(self) == cont_all:
				output.append(lista_items)
				cont = 0
				lista_items = []
		for s in output:
			group_id = False
			procurements = []
			for line in s:  # self
				line = line.with_company(line.company_id)
				if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
					continue
				qty = line._get_qty_procurement(previous_product_uom_qty)
				if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
					continue

				# group_id = line._get_procurement_group()

				if not group_id:
					group_id = self.env['procurement.group'].sudo().create(line._prepare_procurement_group_vals())
					line.order_id.procurement_group_id = group_id
				else:
					# In case the procurement group is already created and the order was
					# cancelled, we need to update certain values of the group.
					updated_vals = {}
					if group_id.partner_id != line.order_id.partner_shipping_id:
						updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
					if group_id.move_type != line.order_id.picking_policy:
						updated_vals.update({'move_type': line.order_id.picking_policy})
					if updated_vals:
						group_id.write(updated_vals)

				values = line._prepare_procurement_values(group_id=group_id)
				product_qty = line.product_uom_qty - qty

				line_uom = line.product_uom
				quant_uom = line.product_id.uom_id
				product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
				procurements.append(self.env['procurement.group'].sudo().Procurement(
					line.product_id, product_qty, procurement_uom,
					line.order_id.partner_shipping_id.property_stock_customer,
					line.name, line.order_id.name, line.order_id.company_id, values))
			if procurements:
				self.env['procurement.group'].sudo().run(procurements)
		#codigo del procurement jit ejecutar de una vez aqui para no usar super
		orders = list(set(x.order_id for x in self))
		for order in orders:
			_logger.warning(f'Este es el ORDER picking {order.picking_ids.read()}')
			count = 1
			for picking in order.picking_ids:
				_logger.warning("Picking: %s" % (picking))
				picking.pagination = count
				count += 1
			reassign = order.picking_ids.filtered(
				lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
			_logger.warning(f'Este es el reassign {reassign}')
			if reassign:
                # Trigger the Scheduler for Pickings
				reassign.sudo().action_confirm()
				reassign.sudo().action_assign()
		return True

		#return super(SaleOrderLineMaxCam, self)._action_launch_stock_rule(previous_product_uom_qty)



	@api.onchange('product_uom_qty', 'product_uom', 'order_id.warehouse_id')
	def _onchange_product_id_check_availability(self):
		_logger.warning("_onchange_product_id_check_availability %s")
		_logger.warning(self.product_id)
		_logger.warning(self.product_uom_qty)
		_logger.warning(self.product_uom)
		_logger.warning(self.order_id.warehouse_id)
		_logger.warning(self.warehouse_id)

		if not self.product_id or not self.product_uom_qty or not self.product_uom:
			#self.product_packaging = False
			return {}
		if self.product_id.type == 'product':
			precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			product = self.product_id.with_context(
				warehouse=self.order_id.warehouse_id.id,
				lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
			)
			product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
			_logger.info("float_compare(product.free_qty, product_qty, precision_digits=precision) %s",float_compare(product.free_qty, product_qty, precision_digits=precision))
			if float_compare(product.free_qty, product_qty, precision_digits=precision) == -1:
				message =  _('Planeas vender %s %s de %s pero solo tienes %s %s disponibles en %s.') % \
						(self.product_uom_qty, self.product_uom.name, self.product_id.name, product.free_qty, product.uom_id.name, self.order_id.warehouse_id.name)
				# We check if some products are available in other warehouses.
				if float_compare(product.free_qty, self.product_id.free_qty, precision_digits=precision) == -1:
					message += _('\nExisten %s %s disponible entre todos los almacenes.\n\n') % \
							(self.product_id.free_qty, product.uom_id.name)
					for warehouse in self.env['stock.warehouse'].search([]):
						quantity = self.product_id.with_context(warehouse=warehouse.id).free_qty
						if quantity > 0:
							message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
				warning_mess = {
					'title': _('No hay suficiente inventario!'),
					'message' : message
				}
				self.product_uom_qty = 0
				return {'warning': warning_mess}
		return {}


	#misma funcion anterior pero retornando True o False
	def _confirm_check_availability_sale(self):
		#if not self.product_id or not self.quantity or not self.warehouse_id:
		#    raise UserError("Producto, cantidad y ALmacen son obligatorios")
		#el almacen tomar el por defecto
		if self.product_id.type == 'product' and self.warehouse_id:
			_logger.info("self.product_id.free_qty arriba %s",self.product_id.free_qty)
			precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			product = self.product_id.with_context(
				warehouse=self.warehouse_id.id,
				lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
			)
			if product.free_qty < self.product_uom_qty:
				another_have = False
				message =  _('Planeas vender %s %s de %s pero solo tienes %s %s disponibles en %s.') % \
						(self.product_uom_qty, self.product_id.uom_id.name, self.product_id.name, product.free_qty, product.uom_id.name, self.warehouse_id.name)
				# We check if some products are available in other warehouses.
				_logger.info("self.product_id.free_qty %s",self.product_id.free_qty)
				"""if product.free_qty < self.product_id.free_qty:
					message += _('\nExisten %s %s disponible entre todos los almacenes.\n\n') % \
							(self.product_id.free_qty, product.uom_id.name)
					for warehouse in self.env['stock.warehouse'].search([]):
						quantity = self.product_id.with_context(warehouse=warehouse.id).free_qty
						if quantity > 0:
							message += "%s: %s %s\n" % (warehouse.name, quantity, self.product_id.uom_id.name)
					another_have = True"""
				#no me interesa decir en la app que hay en otro almacen
				warning_mess = {
					'title': _('No hay suficiente inventario!'),
					'message' : message
				}
				return False,message
				#raise UserError(message)
		return True,''

class StockPickingMaxCam(models.Model):
	_inherit = 'stock.picking'

	pagination = fields.Integer(string="Página",store=True, required=False)
	pages = fields.Integer(string="Numero de páginas", related='sale_id.number_of_pages', store=True)

class AccountMoveMaxCam(models.Model):
	_inherit = 'account.move'

	pagination = fields.Integer(string="Página", compute='_compute_page')
	pages = fields.Integer(string="Número de páginas", compute='_compute_page', store=True)


	def _compute_page(self):
		for record in self:
			for picking in record.picking_ids:
				record.pagination = picking.pagination
				record.pages = picking.pages	
