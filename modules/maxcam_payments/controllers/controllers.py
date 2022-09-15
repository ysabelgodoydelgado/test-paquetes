# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json
from odoo import http, exceptions, fields
from odoo.http import request
from odoo.osv import expression
from datetime import datetime

from dateutil import parser
_logger = logging.getLogger(__name__)
import pytz

class AppPaymentApproval(http.Controller):

	FIELDNAMES = ['id', 'name', 'partner_id', 'amount',
				  'journal_id', 'state', 'seller_id', 'write_date','create_date','payment_approval_line','payment_approval_methods', 'checked']

	FIELD_ORDER_LINE = ['id', 'invoice_id', 'amount', 'journal_id', 'payment_related', 'reference', 
		'payment_date','write_date','invoice_number','total_invoice','total_retention','iva','subtotal','use_balance','amount_balance_use']

	FIELD_ORDER_LINE_METHODS = ['id','amount', 'journal_id']
	FIELDFILTERS = ['id', 'name']

	APPSTATE = {200: 'Success', 400: 'Error',
				409: 'La solicitud no se pudo completar debido a un conflicto del recurso'}


	@http.route('/app/payments_stored', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_payments_stored(self, seller_id, limit=20, offset=0, partner_name=None, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if type(int(seller_id)) == int:


				domain_partner = expression.AND([[('seller_id', '=', int(seller_id))]])
		
				if partner_name:
					domain_partner_name = self._get_search_domain(partner_name)
					domain_partner = expression.AND([domain_partner, domain_partner_name])
				partner = request.env['res.partner'].sudo().search(domain_partner).ids

				domain = expression.AND([[('is_fiscal','=',False),('state', 'in', ['draft', 'process']), ('seller_id', '=', int(seller_id)),('partner_id', 'in', partner)]])

				# Search Read
				_logger.info("domain %s",domain)
				order_ids = request.env['payment.approval'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
																		limit=int(limit), offset=int(offset),
																		order='create_date desc')

				all_sale_count = request.env['payment.approval'].sudo().search_count(domain)
				sale_order_count = len(order_ids)
				if sale_order_count > 0:
					self.convert_field_string(order_ids)
					
					self._get_order_line(order_ids)
					self._get_order_line_methods(order_ids)
					self.convert_field_string_line(order_ids)
					data.update({'data': order_ids, 'count': sale_order_count, 'total_count': all_sale_count})
				else:
					data.update({'status': 204, 'msg': 'No hay recibos', 'count': 0, 'data': False})
		except Exception as e:
			_logger.info("ERROR BUSCANDO PAGOS %s",str(e)) 
			pass

		return json.dumps(data)
	#cambiar http,get y kwargs
	@http.route('/app/add_payment_lot', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_add_payment(self,**kwargs):
		#kwargs = {'payment_approval': {'partner_id': 11921, 'seller_id': 26, 'create_uid': 41, 'payment_approval_methods': [{'journal_id': 13, 'amount': 500, 'reference': 'la ref num', 'date': '2021-09-01T20:52:03.939Z'}, {'journal_id': 13, 'amount': 500, 'reference': '123ert', 'date': '2021-09-01T20:52:31.284Z'}, {'journal_id': 24, 'amount': 200, 'reference': '', 'date': '2021-09-01T20:53:06.536Z'}], 'use_balance': True, 'amount_balance_use': 37.44, 'invoice_lines': [{'invoice_id': 21714, 'amount_residual': 560.64}, {'invoice_id': 22013, 'amount_residual': 507.66}]}} 
		#kwargs = {'payment_approval': {'partner_id': 11921, 'seller_id': 26, 'create_uid': 41, 'payment_approval_methods': [{'journal_id': 29, 'amount': 100, 'reference': 'Efec', 'date': '2021-09-02T17:52:28.078Z'}, {'journal_id': 12, 'amount': 500, 'reference': '123455', 'date': '2021-09-02T17:53:09.014Z'}], 'use_balance': False, 'invoice_lines': [{'invoice_id': 22013, 'amount_residual': 507.66}, {'invoice_id': 22123, 'amount_residual': 42.21}]}}
		
		_logger.info("kwargs============================== %s",kwargs)
		sale_order = kwargs.get('payment_approval')
		_logger.info("este es el payment_approval del kwargs luego del get %s",sale_order)
		#sale_id = sale_order.pop('id', False)
		data = {'status': 200, 'msg': 'Success'}

		create_uid = sale_order.get('create_uid',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)

		if sale_order:
			try:
				success,msg,data_create = self.get_data_to_create(sale_order)
				if success:
					so = request.env['payment.approval'].sudo().create(data_create)
					#confirmar
					if so:
						success,msg = so.sudo().process_payment_batch()
						if not success:
							data.update({'status': 400, 'msg': str(msg)})	
							return data	
					#
					_logger.info("YA CREO PAGO VOY A RETORNAR")
					order_id = request.env['payment.approval'].sudo().search_read(domain=[('id', '=', so.id)],
																	fields=self.FIELDNAMES, limit=1)

					_logger.info("si agrego la nueva linea devolver la info completa %s",order_id)
					if order_id:
						self.convert_field_string(order_id)
						self._get_order_line(order_id)
						self._get_order_line_methods(order_id)
						self.convert_field_string_line(order_id)
							
						data.update({'data': order_id})
						_logger.info('si existe la orden convertira a json las cosas--------------- %s',data)
						return data
				else:
					data.update({'status': 400, 'msg': msg})
					return data

			except Exception as e:
				_logger.warning('Error %s', e)
				_logger.warning('Exeption al internar agregar nuevas lineas')
				data.update({'status': 400, 'msg': str(e)})
				return data



	@http.route(['/app/delete_line_payment'], type='json', auth="public", methods=['PUT'], sitemap=False)
	def delete_line_payment_2(self, payment_id, line_id,create_uid=False):
		data = {'status': 200, 'msg': 'Success'}
		
		_logger.warning("PAYMENTID ANTES DE BUSCAR %s",payment_id)
		so_obj = request.env['payment.approval'].sudo().search([('id', '=', payment_id)]).exists()
		_logger.info("ORDER %s",payment_id)
		_logger.info("LINEA %s",line_id)
		_logger.info("UID %s",create_uid)
		
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
		if so_obj and so_obj.state == 'draft':
			try:
				sol = request.env['payment.approval.line'].sudo().search([('id', '=', line_id),
															  ('payment_approval', '=', so_obj.id)])
												
				_logger.info("PAYMENT LINE LINE %s",sol)
				another_lines = request.env['payment.approval.line']
				if sol and sol.invoice_id:
					another_lines = request.env['payment.approval.line'].sudo().search([('invoice_id', '=', sol.invoice_id.id),
															  ('payment_approval', '=', so_obj.id)])
					if another_lines:
						another_lines.unlink()
					sol.unlink()
			except Exception as e:
				_logger.warning('Error %s', e)
				return data.update({'status': 400, 'msg': e})
		else:
			data = {'status': 200, 'data': None, 'message': 'Recibo de pago ya procesado no se puede modificar '}
		return data


	@http.route(['/app/delete_line_payment_method'], type='json', auth="public", methods=['PUT'], sitemap=False)
	def delete_line_payment_method(self, payment_id, line_id,create_uid=False):
		data = {'status': 200, 'msg': 'Success'}
		
		_logger.warning("PAYMENTID ANTES DE BUSCAR %s",payment_id)
		so_obj = request.env['payment.approval'].sudo().search([('id', '=', payment_id)]).exists()
		_logger.info("ORDER %s",payment_id)
		_logger.info("LINEA %s",line_id)
		_logger.info("UID %s",create_uid)
		
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
		if so_obj and so_obj.state == 'draft':
			try:
				sol = request.env['payment.approval.methods'].sudo().search([('id', '=', line_id),
															  ('payment_approval', '=', so_obj.id)])
												
				_logger.info("PAYMENT LINE LINE %s",sol)
				if sol:
					sol.unlink()
			except Exception as e:
				_logger.warning('Error %s', e)
				return data.update({'status': 400, 'msg': e})
		else:
			data = {'status': 200, 'data': None, 'message': 'Recibo de pago ya procesado no se puede modificar '}
		return data


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
			record.update({'write_date': str(record.get('write_date', False)),
						   'create_date': str(record.get('create_date', False))})

	@staticmethod
	def convert_field_string_line(sale_order):
		for record in sale_order:
			for line in record.get("payment_approval_line"):
				#_logger.info("LINE %s",line)
				line.update({'write_date': str(line.get('write_date', False)),
							'payment_date': str(line.get('payment_date', False))})


	def _get_order_line(self, sale_order):
		for record in sale_order:
			order_line = record.get('payment_approval_line', False)
			#_logger.info("PAYMENT APPROVAL LINE %s",order_line)
			if order_line:
				order = request.env['payment.approval.line'].sudo().search_read(domain=[('id', 'in', order_line)],
																		  fields=self.FIELD_ORDER_LINE)
				#_logger.info("order line encontrada para mandar en la orden %s",order)
				record.update({'payment_approval_line': order})

	def _get_order_line_methods(self, sale_order):
		for record in sale_order:
			order_line = record.get('payment_approval_methods', False)
			#_logger.info("PAYMENT APPROVAL METHODS %s",order_line)
			if order_line:
				order = request.env['payment.approval.methods'].sudo().search_read(domain=[('id', 'in', order_line)],
																		  fields=self.FIELD_ORDER_LINE_METHODS)
				_logger.info("METODOS %s",order)
				record.update({'payment_approval_methods': order})

	def _set_order_line(self, sale_order):
		order_line = sale_order.pop('order_line', False)
		line = []
		for so_line in order_line:
			line.append((0, 0, {'product_id': so_line.get('product_id'),
								'product_uom_qty': so_line.get('product_uom_qty')}))
		sale_order.update({'order_line': line})


	def check_lines_validations_order(self,order):
		_logger.info("lineas a validar %s",order)
		for so_line in order.order_line:
			product = so_line.product_id
			if product and product.free_qty < so_line.product_uom_qty:
				_logger.info("la cantidad no es valida en confirmar")
				return False,'La cantidad de producto %s excede lo disponible (%i)' % (product.name,product.free_qty)
				break
			if product and product.sales_policy > 1 and product.available_qty >= product.sales_policy and so_line.product_uom_qty % product.sales_policy != 0:
				_logger.info("Multiplo invalido en confirmar")
				return False,"El producto %s tiene una Política de Ventas, la cantidad a vender debe ser un múltiplo o igual a %s" % (product.name,product.sales_policy)
				break
		return True,''

	def _set_order_line_diff(self, order_line,methods,sale_order,so_obj):
		#solo vendran lineas nuevas
		try:
			line = []
			for so_line in order_line:
				
				line.append((0, 0, {'invoice_id': so_line.get("invoice_id"),
					'amount':so_line.get("amount",0),
					'journal_id':so_line.get("journal_id",False),
					'reference':so_line.get("reference",False),
					'use_balance':so_line.get("use_balance",False),
					'amount_balance_use':so_line.get("amount_balance_use",0),
					'payment_date':so_line.get("payment_date",False),
					'invoice_number':so_line.get("invoice_number",False),
					'total_retention':so_line.get("total_retention",0),
					'iva':so_line.get("iva",0),
					'subtotal':so_line.get("subtotal",0),
					'partner_id':so_line.get("partner_id",False)
					}))

			sale_order.update({'payment_approval_line': line})
			pm = []
			_logger.info("Estos son los methods recibidos en agregar linea %s",methods)
			for m in methods:
				_logger.info("MMMMMMMMMMMMMMMMM %s",m)
				exist = so_obj.payment_approval_methods.filtered(lambda r: r.journal_id.id == int(m.get("journal_id")))
				_logger.info("EXISTEEEEEEEEEEEEEE %s",exist)
				if not exist:
					pm.append((0, 0, {
						'amount':m.get("amount",0),
						'journal_id':m.get("journal_id",False),
					}))
				else:
					exist.write({'amount':m.get('amount',0)})
					_logger.info("EDITO EL EXISTENTE")
			if len(pm)>0:
				_logger.info("AGREGAR NUEVO METHODO")
			sale_order.update({'payment_approval_methods': pm})
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



	@http.route('/app/balance_partner', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_get_balance_parter(self, partner_id,**kwargs):
		data = {'status': 200, 'msg': 'Success','balance':0}
		try:
			if type(int(partner_id)) == int:
				balance = request.env['account.move'].sudo()._compute_payments_partner_maxcam(partner_id)
				_logger.info("Este es el balanceeeeeeeeeeeeeeee %s",balance)
				data.update({"balance":round(balance,2)})
		except Exception as e:
			_logger.info("ERROR BUSCANDO Balance %s",str(e))
			pass

		return json.dumps(data)

	@http.route('/app/process_payment_approval', type='http', methods=['GET'], auth='public', csrf=False,website=False, sitemap=False)
	def app_process_payment_maxcam(self, payment_id,create_uid,**kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if create_uid:
				request.uid = int(create_uid)
			if type(int(payment_id)) == int:
				pa = request.env['payment.approval'].sudo().browse(int(payment_id))
				if pa:
					success,msg = pa.sudo().process_payment_batch()
					if not success:
						data.update({'status': 400, 'msg': str(msg)})

				else:
					data.update({'status': 400, 'msg': 'Recibo no encontrado'})
		except Exception as e:
			_logger.info("ERROR PROCESANDO PEDIDO %s",str(e))
			data.update({'status': 400, 'msg': str(e)})
		return json.dumps(data)


	@http.route('/app/cancel_payment_approval', type='http', methods=['GET'], auth='public', csrf=False,website=False, sitemap=False)
	def app_cancel_payment_maxcam(self, payment_id,create_uid,**kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if create_uid:
				request.uid = int(create_uid)
			if type(int(payment_id)) == int:
				pa = request.env['payment.approval'].sudo().browse(int(payment_id))
				if pa:
					pa.sudo().cancel_payment()
				else:
					data.update({'status': 400, 'msg': 'Recibo no encontrado'})
		except Exception as e:
			_logger.info("ERROR PROCESANDO cancelar %s",str(e))
			data.update({'status': 400, 'msg': str(e)})
		return json.dumps(data)


	def get_data_to_create(self,data_post):
		_logger.info("Estoy recibiendo %s",data_post)
		invoices = data_post.get('invoice_lines', [])
		methods = data_post.get('payment_approval_methods',[])
		methods_lines = []
		amount_total = 0
		residual_total = 0
		#invoices = [{'invoice_id':22127,"amount_residual":64.93}]
		#methods = [{'amount':200,'journal_id':27,'reference':'referencia prueba merc divisa pago 200'}]
		# {'name': 'linea de pago dos','invoice_id':9,'transfer_number':2,'amount':10,'journal_id':8}
		lines = []
		if len(invoices) == 0:
			return False,'No se recibieron Facturas',False
		for i in invoices:
			#adeudado
			_logger.info("adentro de invoices for %s",i)
			#residual = i.get("amount_residual",0)
			inv = request.env['account.move'].sudo().browse(i.get('invoice_id',False))
			residual = 0
			if inv:
				residual = round(inv.amount_residual,2)
				residual_total +=residual
				i.update({'amount_residual':residual})
			else:
				return False,'Error buscando factura',False

			#sumar el residual general antes de abonar

		#buscar si usar saldo a favor en ese caso mandar a agregar otra linea con los parametros
		#se hace primero con saldo a favor para que en caso de que sobre plata sea de un pago nuevo y no volver a registrar un pago de saldo a favor
		if data_post.get("use_balance",False):
			_logger.info("ADENTRO DE BALANCE ")
			if data_post.get("amount_balance_use")>0:
				amount = data_post.get("amount_balance_use")
				amount_total+= amount
				_logger.info("recorrer facturas")
				for i in invoices:
					_logger.info("Factura adentro de balance")
					residual = i.get("amount_residual",0)
					invoice_id = i.get("invoice_id",False)
					if residual >0 and amount >0:
						if residual > amount:
							#adeudado es mayor a monto usar todo el monto
							lines.append((0, 0, 
								{'invoice_id':invoice_id,
								'amount':amount,
								'use_balance':True,
								'amount_balance_use':amount,
								}))
							residual-=amount
							amount -= amount

							_logger.info("USANDO SALDO INICIAL en caso de residual mayor a monto EL RESIDUAL QUE QUEDA ES %s",residual)
							
							i.update({'amount_residual':residual})
						else:
							#residual <= amount:
							#adeudado es menor o igual a monto usar monto de la factura y descontar
							lines.append((0, 0, 
								{'invoice_id':invoice_id,
								'use_balance':True,
								'amount_balance_use':residual,
								'amount':residual,
								}))
							#descontar del total lo usado
							amount -= residual
							residual-=residual
							_logger.info("USANDO SALDO INICIAL en caso de monto mayor a residual EL RESIDUAL QUE QUEDA ES %s",residual)
							i.update({'amount_residual':residual})


		for m in methods:
			_logger.info("adentro de methods for %s",m)
			amount = m.get("amount",0)
			amount_total += amount
			journal_id = m.get("journal_id",False)
			reference = m.get("reference",False)
			payment_date_t = m.get('payment_date',False)
			payment_date_d = parser.parse(payment_date_t) if payment_date_t else fields.Date.context_today(self) #convertir a datetime obj

			tz = pytz.timezone("America/Caracas")
			payment_date_tz = payment_date_d.astimezone(tz) #representar segun tz
			payment_date = payment_date_tz.date() #tomar solo fecha
			
			_logger.info("fecha recibida %s",payment_date)
			methods_lines.append({
				'journal_id':journal_id,
				'amount':amount,
			})
			for i in invoices:
				#adeudado
				_logger.info("adentro de invoices for %s",i)
				#si se abono con saldo a favor el residual debe ser menor
				residual = i.get("amount_residual",0)
				invoice_id = i.get("invoice_id",False)
				if residual >0 and amount > 0:
					if residual > amount:
						#adeudado es mayor a monto usar todo el monto
						lines.append((0, 0, 
							{'invoice_id':invoice_id,
							'amount':amount,
							'journal_id':journal_id,
							'reference':reference,
							'payment_date':payment_date,
							'memo': str(reference) +':'+str(round(m.get("amount",0),2))
							}))
						residual-=amount
						amount -= amount
						i.update({'amount_residual':residual})
					else:
						#residual <= amount:
						#adeudado es menor o igual a monto usar monto de la factura y descontar
						lines.append((0, 0, 
							{'invoice_id':invoice_id,
							'amount':residual,
							'journal_id':journal_id,
							'reference':reference,
							'payment_date':payment_date,
							'memo': str(reference) +':'+str(round(m.get("amount",0),2))
							}))
						#descontar del total lo usado
						amount -= residual
						residual-=residual
						i.update({'amount_residual':residual})
			m.update({"amount":amount})

		#si sobra saldo y todas las facturas fueron canceladas mandar a hacer un pago directo
		if amount_total + float(data_post.get("amount_balance_use",0)) > residual_total:
			#el total de todos los pagos mas saldo a favor sobra
			for m in methods:
				#buscar cual metodo aun tiene monto a favor
				if m.get("amount",0)>0:
					#hacer un pago directo por lo que sobra
					
					date_t = m.get("payment_date",False)
					date_d = parser.parse(date_t) if date_t else fields.Date.context_today(self)
					
					tz = pytz.timezone("America/Caracas")
					date_tz = date_d.astimezone(tz) #representar segun tz
					date = date_tz.date() #tomar solo fecha
					
					res = {
						"journal_id": m.get("journal_id",False),
						"date": date,
						"ref": str(m.get("reference")) +':'+str(round(m.get("amount",0),2)),
						"amount": m.get("amount"),
						"partner_id": int(data_post.get("partner_id")),
						#'memo': str(amount) + str(reference)
					}
					new_payment = request.env['account.payment'].sudo().create(res)

					if new_payment:
						for ml in methods_lines:
							if ml.get("journal_id",None) == m.get("journal_id",False):
								ml.update({'residual_payment':new_payment.id})
						#new_payment.action_post()
		methods_lines_tuple = []
		for mld in methods_lines:
			methods_lines_tuple.append((
				0,0,mld
			))
		_logger.info("retornar data este es el arreglo de invoices %s",invoices)

		flag_f = False
		for f in invoices:
			if round(f.get('amount_residual',0),2) > 0:
				flag_f = True
				break
		if flag_f:
			return False,'Ocurrio un error con el saldo residual, Por favor intente nuevamente',False
		data = {
			'seller_id': data_post.get('seller_id',False),
			'payment_approval_line':lines,
			'amount':amount_total,
			'partner_id':data_post.get('partner_id',False),
			'payment_approval_methods':methods_lines_tuple,
		}
		return True,'',data