# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json
from odoo import http, exceptions, fields
from odoo.http import request
from odoo.osv import expression
from datetime import datetime

_logger = logging.getLogger(__name__)


class DespositPaymentsMaxcam(http.Controller):

	FIELDNAMES = ['id', 'name', 'amount',
				  'journal_id', 'state', 'seller_id', 'write_date','create_date','payment_approval_lines_ids']

	FIELD_ORDER_LINE = ['id', 'invoice_id', 'partner_id','amount', 'journal_id', 'payment_related', 'reference', 
		'payment_date','write_date','invoice_number','total_invoice','total_retention','iva','subtotal','use_balance','amount_balance_use']
	FIELDFILTERS = ['id', 'name']

	APPSTATE = {200: 'Success', 400: 'Error',
				409: 'La solicitud no se pudo completar debido a un conflicto del recurso'}


	@http.route('/app/lines_cash', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def lines_cash_payments(self, seller_id, limit=100, offset=0, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if type(int(seller_id)) == int:

				domain = [('payment_approval.seller_id','=',int(seller_id)),('payment_approval.state','=','process'),('deposit_id','=',False),('journal_id.type','=','cash')]

				# Search Read
				_logger.info("domain %s",domain)
				order_ids = request.env['payment.approval.line'].sudo().search_read(domain=domain, fields=self.FIELD_ORDER_LINE,
																		limit=int(limit), offset=int(offset),
																		order='create_date desc')

				all_sale_count = request.env['payment.approval.line'].sudo().search_count(domain)
				sale_order_count = len(order_ids)
				_logger.info("LINEAS RETORNADO %s",order_ids)
				if sale_order_count > 0:
					self.convert_field_string_line_cash(order_ids)
					data.update({'data': order_ids, 'count': sale_order_count, 'total_count': all_sale_count})
				else:
					data.update({'status': 204, 'msg': 'No hay Lineas asociadas', 'count': 0, 'data': False})
		except Exception as e:
			_logger.info("ERROR BUSCANDO LINEAS %s",str(e))
			pass

		return json.dumps(data)


	@http.route('/app/deposit_stored', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_deposit_stored(self, seller_id, limit=100, offset=0, partner_name=None, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if type(int(seller_id)) == int:

				domain = expression.AND([[('state', 'in', ['draft', 'confirmed','done']), ('seller_id', '=', int(seller_id))]])

				# Search Read
				_logger.info("domain %s",domain)
				order_ids = request.env['deposit.payment'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
																		limit=int(limit), offset=int(offset),
																		order='create_date desc')

				all_sale_count = request.env['deposit.payment'].sudo().search_count(domain)
				sale_order_count = len(order_ids)
				if sale_order_count > 0:
					self.convert_field_string(order_ids)
					
					self._get_order_line(order_ids)
					self.convert_field_string_line(order_ids)
					data.update({'data': order_ids, 'count': sale_order_count, 'total_count': all_sale_count})
				else:
					data.update({'status': 204, 'msg': 'No hay depositos', 'count': 0, 'data': False})
		except Exception as e:
			_logger.info("ERROR BUSCANDO PAGOS %s",str(e))
			pass

		return json.dumps(data)
	
	@http.route(['/app/delete_line_deposit'], type='json', auth="public", methods=['PUT'], sitemap=False)
	def delete_line_deposit(self, deposit_id, line_id,create_uid=False):
		data = {'status': 200, 'msg': 'Success'}
		
		_logger.warning("DEPOSIT ANTES DE BUSCAR %s",deposit_id)
		so_obj = request.env['deposit.payment'].sudo().search([('id', '=', deposit_id)]).exists()
		_logger.info("DEPOSITO %s",deposit_id)
		_logger.info("LINEA %s",line_id)
		_logger.info("UID %s",create_uid)
		
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)
		if so_obj and so_obj.state == 'draft':
			try:
				for cl in so_obj.payment_approval_lines_ids:
					#_logger.info("LINEA EN FOR DELETE %s",cl)
					if cl.id == int(line_id):
						so_obj.write({'payment_approval_lines_ids':[(3,int(line_id))]
						})
						break

			except Exception as e:
				_logger.warning('Error %s', e)
				return data.update({'status': 400, 'msg': e})
		else:
			data = {'status': 200, 'data': None, 'message': 'Deposito ya procesado no se puede modificar '}
		return data



	@http.route('/app/add_deposit_line', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_add_lines_payment(self,**kwargs):
		#_logger.info("kwargs============================== %s",kwargs)
		sale_order = kwargs.get('deposit_payment')
		_logger.info("este es el deposit_payment del kwargs luego del get %s",sale_order)
		sale_id = sale_order.pop('id', False)
		data = {'status': 200, 'msg': 'Success'}

		create_uid = sale_order.get('create_uid',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)

		if sale_id:
			try:
				#_logger.info("entro en el tryyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
				new_lines = []
				products_ids_order = []

				so = request.env['deposit.payment'].sudo().search([('id', '=', sale_id)])
				if so:
					lines = sale_order.get('payment_approval_lines_ids', [])
					#como saber cual linea es nueva, combinacion de referencia + metodo de pago + factura? en ese caso que la eliminen y hagan de nuevo 
					if len(lines)==0:
						order_id = request.env['deposit.payment'].sudo().search_read(domain=[('id', '=', so.id)],
																	fields=self.FIELDNAMES, limit=1)
						if order_id:
							self.convert_field_string(order_ids)
							
							self._get_order_line(order_ids)
							self.convert_field_string_line(order_ids)
							_logger.info('NADA QUE AGREGAR---------------')
							data.update({'status': 200, 'msg': msg,'data': order_id})
							_logger.info("NO HAY LINEAS QUE AGREGAR %s",data)
							return data
					success,msg = self._set_order_line_diff(lines,sale_order)
					if success:
						so.write(sale_order)
					
						order_id = request.env['deposit.payment'].sudo().search_read(domain=[('id', '=', so.id)],
																		fields=self.FIELDNAMES, limit=1)
						if order_id:
							self.convert_field_string(order_ids)
							self._get_order_line(order_ids)
							self.convert_field_string_line(order_ids)
							
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

	def _set_order_line_diff(self, order_line,sale_order):
		#solo vendran lineas nuevas
		try:
			line = []
			for so_line in order_line:
				#agregar relacion no es crear linea nueva sino enlazar
				line.append((4,int(so_line)))
			sale_order.update({'payment_approval_lines_ids': line})
			return True,''
		except Exception as e:
			_logger.info("error agregando nueva lineas------------- %s",str(e))
			request.env.cr.rollback()
			return False,str(e)
	@staticmethod
	def convert_field_string_line(sale_order):
		for record in sale_order:
			for line in record.get("payment_approval_lines_ids"):
				#_logger.info("LINE %s",line)
				line.update({'write_date': str(line.get('write_date', False)),
							'payment_date': str(line.get('payment_date', False))})

	@staticmethod
	def convert_field_string_line_cash(sale_order):
		for line in sale_order:
			#_logger.info("LINE %s",line)
			line.update({'write_date': str(line.get('write_date', False)),
						'payment_date': str(line.get('payment_date', False))})
	@staticmethod
	def convert_field_string(sale_order):
		for record in sale_order:
			record.update({'write_date': str(record.get('write_date', False)),
						   'create_date': str(record.get('create_date', False))})

	def _get_order_line(self, sale_order):
		for record in sale_order:
			order_line = record.get('payment_approval_lines_ids', False)
			#_logger.info("PAYMENT APPROVAL LINE %s",order_line)
			if order_line:
				order = request.env['payment.approval.line'].sudo().search_read(domain=[('id', 'in', order_line)],
																		  fields=self.FIELD_ORDER_LINE)
				#_logger.info("order line encontrada para mandar en la orden %s",order)
				record.update({'payment_approval_lines_ids': order})
				
	@http.route('/app/cancel_deposit_payment', type='http', methods=['GET'], auth='public', csrf=False,website=False, sitemap=False)
	def app_cancel_deposit_payment_maxcam(self, deposit_id,create_uid,**kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if create_uid:
				request.uid = int(create_uid)
			if type(int(deposit_id)) == int:
				pa = request.env['deposit.payment'].sudo().browse(int(deposit_id))
				if pa:
					pa.sudo().cancel_deposit()
				else:
					data.update({'status': 400, 'msg': 'Deposito no encontrado'})
		except Exception as e:
			_logger.info("ERROR PROCESANDO deposito cancelar %s",str(e))
			data.update({'status': 400, 'msg': str(e)})
		return json.dumps(data)

	@http.route('/app/process_deposit_payment', type='http', methods=['GET'], auth='public', csrf=False,website=False, sitemap=False)
	def app_process_deposit_maxcam(self, deposit_id,create_uid,**kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if create_uid:
				request.uid = int(create_uid)
			if type(int(deposit_id)) == int:
				pa = request.env['deposit.payment'].sudo().browse(int(deposit_id))
				
				if pa:
					validated,msg = self.validated_deposit(pa)
					#validated = True
					#msg = ''
					if not validated:
						data.update({'status': 400, 'msg': msg})
					else:
						pa.sudo().processs_deposit()
				else:
					data.update({'status': 400, 'msg': 'Recibo no encontrado'})
		except Exception as e:
			_logger.info("ERROR PROCESANDO PEDIDO %s",str(e))
			data.update({'status': 400, 'msg': str(e)})
		return json.dumps(data)

	def validated_deposit(self,d):
		parents = []
		if not d or not d.seller_id.journal_id_maxcam:
			return False,''
		for line in d.payment_approval_lines_ids:
			if line.payment_approval not in parents:
				parents.append(line.payment_approval)
		payments = []
		for p in parents:
			#metodos de pago del diario del vendedor unicamente
			payments.append(p.payment_approval_methods.filtered_domain([('journal_id', '=', d.seller_id.journal_id_maxcam.id)]))
		total = sum([pay.amount for pay in payments]) if len(payments) > 0 else 0

		_logger.info("TOTAL %s",total)

		_logger.info("amount %s",d.amount)
		if round(total,2) > round(d.amount,2):
			return False,"El monto indicado en el deposito es menor al reportado en los metodos de pago de los recibos"
		return True,''
