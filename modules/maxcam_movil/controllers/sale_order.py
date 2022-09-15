# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import json
from odoo import http, exceptions, fields
from odoo.http import request
from odoo.osv import expression
from datetime import datetime

_logger = logging.getLogger(__name__)

from odoo.addons.maxcam_movil.controllers.functions import check_access
class AppSaleOrder(http.Controller):

	FIELDNAMES = ['id', 'name', 'partner_id', 'partner_invoice_id', 'partner_shipping_id', 'validity_date',
				  'date_order', 'pricelist_id', 'payment_term_id', 'order_line', 'amount_untaxed', 'amount_tax',
				  'amount_total', 'state', 'note', 'invoice_status', 'state_seller','tax_id_maxcam']

	FIELD_ORDER_LINE = ['id', 'product_template_id', 'name', 'product_uom_qty', 'brand_id', 'price_unit', 'tax_id',
						'price_subtotal', 'product_id']
	FIELDFILTERS = ['id', 'name']

	APPSTATE = {200: 'Success', 400: 'Error',
				409: 'La solicitud no se pudo completar debido a un conflicto del recurso'}

	@http.route(['/app/sale_order/<int:sale_order_id>/print'], type='http', methods=['GET'], auth="public", website=False,
				sitemap=False)
	def print_saleorder(self, sale_order_id, **kwargs):
		try:
			sale_order = request.env['sale.order'].sudo().search([('id', '=', int(sale_order_id))])
		except Exception as e:
			_logger.info('%s', e)
			return json.dumps({'status': 400, 'msg': str(e)})
		if sale_order:
			request.uid = int(2)
			pdf, _ = request.env.ref('sale.action_report_saleorder').sudo()._render_qweb_pdf([sale_order_id])
			pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
			return request.make_response(pdf, headers=pdfhttpheaders)

	@http.route('/app/sale_order', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_sale_order_movil(self, seller_id, limit=20, offset=0, partner_name=None, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		if type(int(seller_id)) == int:
			domain_partner = expression.AND([[('seller_id', '=', int(seller_id))]])
			if partner_name:
				domain_partner_name = self._get_search_domain(partner_name)
				domain_partner = expression.AND([domain_partner, domain_partner_name])
			partner = request.env['res.partner'].sudo().search(domain_partner).ids

			domain = expression.AND([[('state', 'in', ['draft', 'sent', 'sale', 'done']), ('partner_id', 'in', partner)]])
			for key in kwargs:
				if key in self.FIELDFILTERS:
					if key == 'name':
						search_domain = self._get_search_domain(kwargs.get(key))
						domain = expression.AND([domain, search_domain])
					else:
						value = kwargs.get(key)
						domain = expression.AND([domain, [(key, '=', int(value))]])

			# Search Read
			order_ids = request.env['sale.order'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
																	 limit=int(limit), offset=int(offset),
																	 order='create_date desc')
			all_sale_count = request.env['sale.order'].sudo().search_count(domain)
			sale_order_count = len(order_ids)
			if sale_order_count > 0:
				self.convert_field_string(order_ids)
				self._get_order_line(order_ids)
				data.update({'data': order_ids, 'count': sale_order_count, 'total_count': all_sale_count})
			else:
				data.update({'status': 204, 'msg': 'No hay presupuestos asociados', 'count': 0, 'data': False})

		return json.dumps(data)
	#decorador para verificar que no este bloqueado
	#@validate_access_seller
	@http.route('/app/add_order_lines', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_add_lines_order(self,**kwargs):
		sale_order = kwargs.get('sale_order')
		sale_id = sale_order.pop('id', False)
		data = {'status': 200, 'msg': 'Success'}
		
		if sale_order.get("payment_term_id",False) == 69:
			sale_order.update({"payment_term_id":False})
		create_uid = sale_order.get('user_id',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
			can_access,msg = check_access(create_uid)
			if not can_access:
				return {'status': 401, 'msg': msg}
		if sale_id:
			try:
				new_lines = []
				products_ids_order = []

				so = request.env['sale.order'].sudo().search([('id', '=', sale_id)])
				if so:
					for line in so.order_line:
						if line.product_id and line.product_id.id not in products_ids_order:
							products_ids_order.append(line.product_id.id)

					lines = sale_order.get('order_line', False)
					#chequear que todas las lineas tengan disponibilidad, al encontrar una sin disponibilidad retornara false
					if lines:
						success_all,msg = self.check_lines_validations(lines)
						if not success_all:
							order_id = request.env['sale.order'].sudo().search_read(domain=[('id', '=', so.id)],
																		fields=self.FIELDNAMES, limit=1)
							if order_id:
								self.convert_field_string(order_id)
								self._get_order_line(order_id)
								data.update({'status': 400, 'msg': msg,'data': order_id})
								return data
							else:
								data.update({'status': 400, 'msg': msg})
								return data

						for so_line in lines:
							product_id = so_line.get('product_id', False)
							if product_id and product_id not in products_ids_order:
								new_lines.append(so_line)

					if len(new_lines)==0:
						order_id = request.env['sale.order'].sudo().search_read(domain=[('id', '=', so.id)],
																	fields=self.FIELDNAMES, limit=1)
						if order_id:
							self.convert_field_string(order_id)
							self._get_order_line(order_id)
							data.update({'status': 200, 'msg': msg,'data': order_id})
							return data
					success,msg = self._set_order_line_diff(new_lines,sale_order)
					if success:
						so.write(sale_order)
					
						order_id = request.env['sale.order'].sudo().search_read(domain=[('id', '=', so.id)],
																		fields=self.FIELDNAMES, limit=1)
						if order_id:
							self.convert_field_string(order_id)
							self._get_order_line(order_id)
							
							data.update({'data': order_id})
							return data
					else:
						data.update({'status': 400, 'msg': msg})
						return data

				_logger.warning('Despues de _set_order_line en el primer try en endpoint nuevo')
			except Exception as e:
				_logger.warning('Error %s', e)
				_logger.warning('Exeption al internar agregar nuevas lineas')
				data.update({'status': 400, 'msg': str(e)})
				return data
	#@validate_access_seller
	@http.route('/app/edit_order', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_edit_order_movil(self, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		sale_order = kwargs.get('sale_order')
		if sale_order.get("payment_term_id",False) == 69:
			sale_order.update({"payment_term_id":False})
		sale_id = sale_order.pop('id', False)
		order_line = sale_order.pop('order_line',False)
		create_uid = sale_order.get('user_id',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
			can_access,msg = check_access(create_uid)
			if not can_access:
				return {'status': 401, 'msg': msg}
		try:
			if sale_id:
				so = request.env['sale.order'].sudo().search([('id', '=', sale_id)])
				if so:
					so.write(sale_order)
					return data
			else:
				data.update({'status': 400, 'msg': 'Orden no existe'})
				return data
		except Exception as e:
			_logger.info("error editando orden")
			data.update({'status': 400, 'msg': str(e)})
			return data
	#@validate_access_seller
	@http.route('/app/create_order', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_create_order_movil(self, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		sale_order = kwargs.get('sale_order')
		sale_id = sale_order.pop('id', False)
		method = request.httprequest.method
		create_uid = sale_order.get('user_id',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
			can_access,msg = check_access(create_uid)
			if not can_access:
				return {'status': 401, 'msg': msg}
		# comprobamos productos duplicados
		if not self.product_duplicate(sale_order):
			data.update({'status': 400, 'msg': 'Existen productos duplicasdos'})
			return data
		if sale_id:
			try:
				so = request.env['sale.order'].sudo().search([('id', '=', sale_id)])
				so.order_line.unlink()
				self._set_order_line(sale_order)
			except Exception as e:
				_logger.warning('Error %s', e)
				_logger.warning('Exeption al internar eliminar y volver a setar lineas')
				data.update({'status': 400, 'msg': str(e)})
				return data
		else:
			self._set_order_line(sale_order)
			sale_order.update({'date_order': datetime.today()})

		mso = request.env['sale.order'].sudo()
		so = False
		try:
			if method == 'POST':
				so = mso.create(sale_order)
				data.update({'data': so})
			elif method == 'PUT':
				so = mso.search([('id', '=', sale_id)])
				so.write(sale_order)
				# so.onchange_partner_id()
				# so.onchange_partner_shipping_id()
				# so._compute_tax_id()
				_logger.warning("el metodo es PUT se edito la orden")
				data.update({'data': so.id})
		except Exception as e:
			_logger.warning('Error %s', e)
			_logger.warning('El exepction del try post o put')
			return data.update({'status': 400, 'msg': str(e)})
		if so:
			order_id = request.env['sale.order'].sudo().search_read(domain=[('id', '=', so.id)],
																	fields=self.FIELDNAMES, limit=1)
			if order_id:
				self.convert_field_string(order_id)
				self._get_order_line(order_id)
				data.update({'data': order_id})
		else:
			data.update({'status': 400, 'msg': 'Error al crear presupuesto', 'count': 0, 'data': False})
		return data
	#@validate_access_seller
	@http.route(['/app/order/delete_line'], type='json', auth="public", methods=['PUT'], sitemap=False)
	def update_order(self, sale_order_id, line_id,uid=False):
		data = {'status': 200, 'msg': 'Success'}

		so_obj = request.env['sale.order'].sudo().search([('id', '=', sale_order_id)]).exists()
		if uid:
			#request.session.uid = int(create_uid)
			request.uid = int(uid)
			can_access,msg = check_access(uid)
			if not can_access:
				return {'status': 401, 'msg': msg}
		if so_obj and so_obj.state == 'draft':
			try:
				sol = request.env['sale.order.line'].sudo().search([('id', '=', line_id),
															  ('order_id', '=', so_obj.id)])

				sol.unlink()
			except Exception as e:
				_logger.warning('Error %s', e)
				return data.update({'status': 400, 'msg': e})
		else:
			data = {'status': 200, 'data': None, 'message': 'Cotizacion ya procesada no se puede modificar '}
		return data
	#@validate_access_seller
	@http.route('/app/sale_order/action/<int:sale_id>', type='json', methods=['POST', 'PUT'], auth='public', website=False,
				sitemap=False)
	def app_confirm_cancel_order_movil(self, sale_id=0, confirm=False, uid=False,tax_id_maxcam=False,**kwargs):
		data = {'status': 200, 'msg': 'Success'}
		_logger.info("uid CONFIRM %s",uid)
		try:
			if uid:
				#request.session.uid = int(create_uid)
				request.uid = int(uid)
				can_access,msg = check_access(uid)
				if not can_access:
					return {'status': 401, 'msg': msg}
			if sale_id > 0:
				so = request.env['sale.order'].sudo().search([('id', '=', sale_id)])
				if confirm == 'confirm':
					success,msg = self.check_lines_validations_order(so)
					if success:
						if tax_id_maxcam:
							#agregar impuesto a cada linea
							self.add_tax_lines(so,tax_id_maxcam)
							#si lleva impuesto requiere factura
							so.write({'can_send_to_admin':True})
						so.action_confirm()
						so._create_analytic_account()  # normally created at so confirmation when you use the right products
					else:
						data.update({'status': 400, 'msg': msg})
						return data
				elif confirm == 'cancel':
					so = request.env['sale.order'].sudo().search([('id', '=', sale_id)])
					so.action_cancel()
		except Exception as e:
			_logger.warning('Error %s', e)
			data.update({'status': 400, 'msg': e})
		return data


	def add_tax_lines(self,so,tax_id_maxcam):
		for line in so.order_line:
			line.write({'tax_id':[(6, 0, [int(tax_id_maxcam)])]})
	@staticmethod
	def _get_search_domain(search):
		domain = []
		if search:
			for srch in search.split(" "):
				domain.append([('name', 'ilike', srch)])
		return expression.OR(domain)

	@staticmethod
	def convert_field_string(sale_order):
		for record in sale_order:
			record.update({'date_order': str(record.get('date_order', False)),
						   'validity_date': str(record.get('validity_date', False))})

	def _get_order_line(self, sale_order):
		for record in sale_order:
			order_line = record.get('order_line', False)
			if order_line:
				order = request.env['sale.order.line'].sudo().search_read(domain=[('id', 'in', order_line)],
																		  fields=self.FIELD_ORDER_LINE)
				record.update({'order_line': order})

	def _set_order_line(self, sale_order):
		order_line = sale_order.pop('order_line', False)
		line = []
		for so_line in order_line:
			line.append((0, 0, {'product_id': so_line.get('product_id'),
								'product_uom_qty': so_line.get('product_uom_qty')}))
		sale_order.update({'order_line': line})

	def check_lines_validations(self,lines):
		for so_line in lines:
			product = request.env['product.product'].sudo().browse(int(so_line.get('product_id')))
			
			warehouse_id = request.env['stock.warehouse'].sudo().search([('is_sale_storage','=',True)],limit=1)
			if warehouse_id:
				product = product.with_context(
					warehouse=warehouse_id.id,
				)
			if product and product.free_qty < so_line.get('product_uom_qty'):
				return False,'La cantidad de producto %s excede lo disponible (%i)' % (product.name,product.free_qty)
				break
			if product and product.sales_policy > 1 and product.available_qty >= product.sales_policy and so_line.get('product_uom_qty') % product.sales_policy != 0:
				return False,"El producto %s tiene una Política de Ventas, la cantidad a vender debe ser un múltiplo o igual a %s" % (product.name,product.sales_policy)
				break
		return True,''

	def check_lines_validations_order(self,order):
		for so_line in order.order_line:
			product = so_line.product_id

			#if product and product.free_qty < so_line.product_uom_qty:
			#	_logger.info("la cantidad no es valida en confirmar")
			#	return False,'La cantidad de producto %s excede lo disponible (%i)' % (product.name,product.free_qty)
			#	break
			success,msg = so_line._confirm_check_availability_sale()
			if not success:
				return False,msg
				break
			if product and product.sales_policy > 1 and product.available_qty >= product.sales_policy and so_line.product_uom_qty % product.sales_policy != 0:
				_logger.info("Multiplo invalido en confirmar")
				return False,"El producto %s tiene una Política de Ventas, la cantidad a vender debe ser un múltiplo o igual a %s" % (product.name,product.sales_policy)
				break
		return True,''

	def _set_order_line_diff(self, order_line,sale_order):
		#ya aqui deben venir validado que todos tengan disponibilidad
		try:
			line = []
			for so_line in order_line:
				line.append((0, 0, {'product_id': so_line.get('product_id'),
									'product_uom_qty': so_line.get('product_uom_qty')}))
			sale_order.update({'order_line': line})
			return True,''
		except Exception as e:
			_logger.info("error agregando nueva lineas------------- %s",str(e))
			request.env.cr.rollback()
			return False,str(e)

	def product_duplicate(self, sale_order):
		product_ids = []
		lines = sale_order.get('order_line', False)
		flag = True
		if lines:
			for so_line in lines:
				product_id = so_line.get('product_id', False)
				if product_id and product_id not in product_ids:
					product_ids.append(product_id)
				else:
					flag = False
		return flag
