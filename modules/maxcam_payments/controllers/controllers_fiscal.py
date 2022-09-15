# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json
from odoo import http, exceptions, fields
from odoo.http import request
from odoo.osv import expression
from datetime import datetime

_logger = logging.getLogger(__name__)
from odoo.addons.binaural_restful.common import (
	extract_arguments,
	invalid_response,
	valid_response,
)
from odoo.exceptions import AccessError
import math
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings
import calendar
import time
from dateutil import parser
import pytz
class AppPaymentApprovalFiscal(http.Controller):


	FIELDNAMES = ['id', 'name', 'partner_id', 'amount',
				  'journal_id', 'state', 'seller_id', 'write_date','create_date','payment_approval_line','payment_approval_methods', 'checked']

	FIELD_ORDER_LINE = ['id', 'invoice_id', 'amount', 'journal_id', 'payment_related', 'reference', 
		'payment_date','write_date','invoice_number','total_invoice','total_retention','iva','subtotal','use_balance','amount_balance_use']

	FIELD_ORDER_LINE_METHODS = ['id','amount', 'journal_id']
	FIELDFILTERS = ['id', 'name']

	APPSTATE = {200: 'Success', 400: 'Error',
				409: 'La solicitud no se pudo completar debido a un conflicto del recurso'}


	@http.route('/app/get_rate_fiscal', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def get_rate_fiscal(self, limit=20, offset=0, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		tax = request.env['account.tax'].sudo().search([('in_app','=',True)],limit=1)
		if tax:
			d = {'id':tax.id,'amount':tax.amount,'name':tax.name}
			data.update({'data': d})
		else:
			data.update({'status': 204, 'msg': 'Tasa no encontrada','data': False})
		return json.dumps(data)
	
	@http.route('/app/invoices_fiscal', type="http", auth="none", methods=["GET"], csrf=False,website=False, sitemap=False)
	def get_fiscal_invoices(self, partner_id=None, id=None, **payload):
		self._model = "ir.model"
		model = 'account.move'
		try:
			ioc_name = model
			fields=['id', 'name','amount_residual', 'sent_to_admin']
			domain=[('partner_id','=',int(partner_id)),('state','=','posted'),('amount_residual','>',0),('move_type', '=', 'out_invoice'),('sent_to_admin','=',True),('reception_date_client','!=',False)]
			#para test sin partner
			#domain=[('state','=','posted'),('amount_residual','>',0),('move_type', '=', 'out_invoice'),('sent_to_admin','=',True)]
			model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
			if model:
				#domain, fields, offset, limit, order = extract_arguments(payload)
				#data = request.env[model.model].sudo().search_read(
				#	domain=domain, fields=fields, offset=offset, limit=limit, order=order,
				#)
				#test, rmeover limit
				data = request.env[model.model].sudo().search_read(domain=domain,fields=fields)
				_logger.info("DATAAAAAAA %s",data)
				if data:
					#_logger.info("TRAJO DATA ahora devolver el monto de retencion de cada una y si tiene o no %s",data)
					self.process_notes_fiscal(data)
					return valid_response(data)
				else:
					return valid_response(data)
			return invalid_response(
				"invalid object model", "The model %s is not available in the registry." % ioc_name,
			)
		except AccessError as e:

			return invalid_response("Access error", "Error: %s" % e.name)
	
	def process_notes_fiscal(self,data):
		_logger.info("Data recibida de busqueda")
		for i in data:
			_logger.info("NOTA %s",i)
			invoice = request.env['account.move'].sudo().browse(i.get('id',False))
			if invoice:
				#nno es exento buscar %
				if not invoice.partner_id.exempt_iva and invoice.partner_id.withholding_type:
					percent = invoice.partner_id.withholding_type.value
					#amount_tax
					retention = invoice.amount_tax * (percent/100)
					i.update({'amount_retention':retention,'amount_taxed':invoice.amount_tax,'amount_base':invoice.amount_untaxed})
					_logger.info("este es el monto retenidoooooooooooooooooooooooooo %s",percent)
				else:
					i.update({'amount_retention':0,'amount_taxed':invoice.amount_tax,'amount_base':invoice.amount_untaxed})
			#buscar la nota, el partner y calcular la retencion


	@http.route('/app/payments_stored_fiscal', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_payments_stored(self, seller_id, limit=20, offset=0, partner_name=None, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		try:
			if type(int(seller_id)) == int:
				domain_partner = expression.AND([[('seller_id', '=', int(seller_id))]])
		
				if partner_name:
					domain_partner_name = self._get_search_domain(partner_name)
					domain_partner = expression.AND([domain_partner, domain_partner_name])
				partner = request.env['res.partner'].sudo().search(domain_partner).ids
				domain = expression.AND([[('is_fiscal','=',True),('state', 'in', ['draft', 'process']), ('seller_id', '=', int(seller_id)),('partner_id', 'in', partner)]])

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
			data.update({'data': [], 'count': 0, 'total_count': 0})
			pass

		return json.dumps(data)
	#cambiar http,get y kwargs
	#json POST
	@http.route('/app/add_payment_lot_fiscal', type='json', methods=['POST', 'PUT'], auth='public', website=False, sitemap=False)
	def app_add_payment_fiscal(self,**kwargs):
		#kwargs = ""
		#_logger.info("kwargs============================== %s",kwargs)POST
		sale_order = kwargs.get('payment_approval')
		_logger.info("este es el payment_approval del kwargs luego del get %s",sale_order)
		
		#sale_order = {'partner_id': 11921, 'seller_id': 26, 'create_uid': 41, 'use_balance': True, 'amount_balance_use': 1671.91, 'invoice_lines': [{'invoice_id': 34818, 'amount_retention': 494.56499999999994, 'image': '/9j/4QrvRXhpZgAASUkqAAgAAAALABABAgASAAAAkgAAAAABBAABAAAA4AEAAAEBBAABAAAA4AEAADIBAgAUAAAApAAAABIBAwABAAAAAQAAABMCAwABAAAAAQAAAGmHBAABAAAA0AAAACgBAwABAAAAAgAAABoBBQABAAAAuAAAABsBBQABAAAAwAAAAA8BAgAIAAAAyAAAAK4BAABTYW1zdW5nIEdhbGF4eSBTOQAyMDIxOjA5OjE3IDE2OjEyOjQyAEgAAAABAAAASAAAAAEAAAB1bmtub3duAA4AkpICAAQAAAA4NTUAkZICAAQAAAA4NTUAkJICAAQAAAA4NTUACpIFAAEAAAB+AQAACZIDAAEAAAAAAAAABJACABQAAACGAQAAA6AEAAEAAADgAQAAA5ACABQAAACaAQAAA6QDAAEAAAAAAAAAAqAEAAEAAADgAQAAAZEHAAQAAAABAgMAAaADAAEAAAD//wAAAJAHAAQAAAAwMjIwAKAHAAQAAAAwMTAwAAAAACQTAADoAwAAMjAyMTowOToxNyAxNjoxMjo0MgAyMDIxOjA5OjE3IDE2OjEyOjQyAAIAAQIEAAEAAADMAQAAAgIEAAEAAAAbCQAAAAAAAP/Y/+AAEEpGSUYAAQEAAAEAAQAA/9sAQwAFAwQEBAMFBAQEBQUFBgcMCAcHBwcPCwsJDBEPEhIRDxERExYcFxMUGhURERghGBodHR8fHxMXIiQiHiQcHh8e/9sAQwEFBQUHBgcOCAgOHhQRFB4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4e/8AAEQgA8AFAAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/aAAwDAQACEQMRAD8A+TKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKdGjyOEjRndjgKoySabXWaLL/YXg6TWrdFN/dXH2eGQjPlKBkke/B/Sg68Fho4io1OVopNt76Lsu/RGBdaTqlrD51zp13DF3d4WAH4kVUhjkmlSKJC8jsFVQMkk9BW5pfizWbS9Wae9muoSf3sMzblde4wen4V0OnaXZ2PxTjhhUCBkM8KdlJQnH4HOPwoO+hl1DF8rw8nbmjF3tpzOyatv6dNNzJm0XQdGVY9fv7mW9IBa2sgp8vPZmPGaQaFpGrW8r+HL24a5iXebO6UB2H+yRwfpXO3ss095NNcEmV5GZyfUk5q74Tlli8Tac8BO/7Si8dwTgj8iaAhi8PKuqPsVyN2681tr379e1+ltDMIIJBGCKK1vGMccfinUkiAC+exwPU8n9ayaDzMVQ+r150r35W19zsFFFFBgFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFdJ4dvtOutFm8P6vMbaJpfOtrnGRG+MYI9P8TXN0UHRhcTLDVOeKT6NPZp7p/16HV2vh7SLKdbrVPEGnTWqHd5VtJveX2x2zWfqXiG4uPFX9uQL5bJIDEh7KOAD9R1+prEooOmrmF4ezoQUI3vo222ttW+nRfqdbfadoviCZtQ03VbXT55TumtbttgVj1Kt3B/zjpUmnxaN4WY6hNqFvqmpICLeG3O6NGIxuZv8/wCHHUUG/wDasVP2yox9p/Nrv35b2v8AhfWxJczSXFxJcTNuklcu7epJyajoooPIbcnd7hRRRQIKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigD//2f/gABBKRklGAAEBAAABAAEAAP/bAEMAAgEBAQEBAgEBAQICAgICBAMCAgICBQQEAwQGBQYGBgUGBgYHCQgGBwkHBgYICwgJCgoKCgoGCAsMCwoMCQoKCv/bAEMBAgICAgICBQMDBQoHBgcKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCv/AABEIAeAB4AMBIgACEQEDEQH/xAAVAAEBAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8Ah+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD//2Q==', 'note': 'you know', 'amount_residual': 764.92}]} 
		data = {'status': 200, 'msg': 'Success'}

		create_uid = sale_order.get('create_uid',False)
		if create_uid:
			#request.session.uid = int(create_uid)
			request.uid = int(create_uid)

		if sale_order:
			#if 1 == 1:
			try:
				success,msg,data_create = self.get_data_to_create_fiscal(sale_order)
				if success:
					_logger.info("Esta es la data a crear %s",data_create)
					so = request.env['payment.approval'].sudo().create(data_create)
					if so:
						success,msg = so.sudo().process_payment_batch()
						if not success:
							data.update({'status': 400, 'msg': str(msg)})	
							return data	
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


	@staticmethod
	def convert_field_string(sale_order):
		for record in sale_order:
			record.update({'write_date': str(record.get('write_date', False)),
						   'create_date': str(record.get('create_date', False))})

	@staticmethod
	def convert_field_string_line(sale_order):
		_logger.info("convert_field_string_line")
		for record in sale_order:
			for line in record.get("payment_approval_line"):
				_logger.info("convert_field_string_line %s",line)
				line.update({'write_date': str(line.get('write_date', False)),
							'payment_date': str(line.get('payment_date', False))})

	def _get_order_line(self, sale_order):
		_logger.info("_get_order_line")
		for record in sale_order:
			order_line = record.get('payment_approval_line', False)
			_logger.info("PAYMENT APPROVAL LINE %s",order_line)
			if order_line:
				order = request.env['payment.approval.line'].sudo().search_read(domain=[('id', 'in', order_line)],
																		  fields=self.FIELD_ORDER_LINE)
				#_logger.info("order line encontrada para mandar en la orden %s",order)
				record.update({'payment_approval_line': order})

	def _get_order_line_methods(self, sale_order):
		_logger.info("_get_order_line_methods")
		for record in sale_order:
			order_line = record.get('payment_approval_methods', False)
			_logger.info("PAYMENT APPROVAL METHODS %s",order_line)
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


	def get_data_to_create_fiscal(self,data_post):
		#_logger.info("Estoy recibiendo %s",data_post)
		invoices = data_post.get('invoice_lines', [])
		methods = data_post.get('payment_approval_methods',[])
		methods_lines = []
		amount_total = 0
		residual_total = 0
		if len(invoices) == 0:
			return False,'No se recibieron Facturas',False
		#invoices = [{'invoice_id':22127,"amount_residual":64.93}]
		#methods = [{'amount':200,'journal_id':27,'reference':'referencia prueba merc divisa pago 200'}]
		# {'name': 'linea de pago dos','invoice_id':9,'transfer_number':2,'amount':10,'journal_id':8}
		lines = []
		retenciones = []
		for i in invoices:
			#adeudado
			#_logger.info("adentro de invoices for %s",i)
			#residual = i.get("amount_residual",0)
			inv = request.env['account.move'].sudo().browse(i.get('invoice_id',False))
			residual = 0
			if inv:
				residual = round(inv.amount_residual,2)
				#residual_total +=residual
				#i.update({'amount_residual':residual})
			else:
				return False,'error obteniendo factura',False
			#if i.get("amount_retention",0)>0:
			if residual >0:
				retenciones.append({
					'invoice_id':i.get("invoice_id"),
					'amount_retention':i.get("amount_retention",0),
					'image':i.get("image",False),
					'seller_id':data_post.get("seller_id"),
					'note':i.get('note',''),
				})
				residual -= i.get("amount_retention",0)
				i.update({'amount_residual':residual})
				#esta factura tiene retencion descontarlo del monto y ponerlo aparte en una lista
			residual_total +=residual
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
							i.update({'amount_residual':residual})

		#----------------------------------------------------- inicio de retencion
		#si la factura tiene retencion y mandaron imagen hay que cargar la retencion en un modelo y hacer el asiento y cruzar ese asiento con la factura
		_logger.info("mandare a hacer retenciones")
		cont_ret = 1
		if len(retenciones)>0:
			for r in retenciones:
				move_ret,invoice = self.make_retention(r,cont_ret)
				cont_ret+=1
				ret_register = self.register_retention(r,move_ret,invoice)
				#registrar en el modelo nuevo, aun no se ha confirmado el asiento de retencion
				
		#-------------------------------------------------------fin de retencion

		for m in methods:
			_logger.info("adentro de methods for %s",m)
			amount = m.get("amount",0)
			amount_total += amount
			journal_id = m.get("journal_id",False)
			reference = m.get("reference",False)
			payment_date_t = m.get('payment_date',False)
			payment_date_d = parser.parse(payment_date_t) if payment_date_t else fields.Date.context_today(self)
			 
			tz = pytz.timezone("America/Caracas")
			payment_date_tz = payment_date_d.astimezone(tz) #representar segun tz
			payment_date = payment_date_tz.date() #tomar solo fecha

			methods_lines.append({
				'journal_id':journal_id,
				'amount':amount,
			})
			for i in invoices:
				#adeudado
				#_logger.info("adentro de invoices for %s",i)
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
							'memo': str(reference) +':'+str(m.get("amount",0)) 
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
							'memo': str(reference) +':'+str(m.get("amount",0)) 
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
						#"payment_type": self.payment_type,
						"amount": m.get("amount"),
						"partner_id": int(data_post.get("partner_id")),

					}
					new_payment = request.env['account.payment'].sudo().create(res)
					if new_payment:
						for ml in methods_lines:
							if ml.get("journal_id",None) == m.get("journal_id",False):
								ml.update({'residual_payment':new_payment.id})
						#new_payment.action_post()

		_logger.info("retornar data, methos lines %s",methods_lines)
		methods_lines_tuple = []
		for mld in methods_lines:
			methods_lines_tuple.append((
				0,0,mld
			))
		_logger.info("retornar data linea 419")
		#_logger.info("retornar data este es el arreglo de invoices %s",invoices)

		flag_f = False
		for f in invoices:
			_logger.info("round(f.get('amount_residual',0),2) %s",round(f.get('amount_residual',0),2))
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
			'is_fiscal':True,
		}
		return True,'',data

	def make_retention(self,retention,cont_ret):
		_logger.info("funcion hacer retencion")
		line_ret = []
		invoice_id = request.env['account.move'].sudo().browse(retention.get("invoice_id",False))
		if invoice_id:
			amount_edit = retention.get("amount_retention",0)
			cxc = False
			for cta in invoice_id.line_ids:
				if cta.account_id.user_type_id.type == 'receivable':
					cxc = cta.account_id.id
			journal = int(request.env['ir.config_parameter'].sudo().get_param('journal_retention_client_maxcam'))
			_logger.info("buscar decimal place")
			company = request.env['res.company'].sudo().search([],limit=1)
			_logger.info("company %s",company)
			decimal_places = company.currency_id.decimal_places
			partner_id = invoice_id.partner_id
			_logger.info("agregr line ret")
			line_ret.append((0, 0, {
				'name': 'Cuentas por Cobrar Cientes (R)',
				'account_id': cxc,
				'partner_id': partner_id.id,
				'debit': 0,
				'credit': self.round_half_up(amount_edit,decimal_places),
			}))
			line_ret.append((0, 0, {
				'name': 'RC-'+str(invoice_id.name),
				'account_id': partner_id.iva_retention.id,
				'partner_id': partner_id.id,
				'debit': self.round_half_up(amount_edit,decimal_places),
				'credit': 0,
			}))
			# Asiento Contable
			if len(line_ret)>0:
				ts = calendar.timegm(time.gmtime())
				move_obj = request.env['account.move'].sudo().create({
					'ref': 'RIV-'+ str(invoice_id.name),#aqui
					'name':'RIV-'+str(ts) +'-'+str(cont_ret),
					'date': fields.Date.today(),
					'journal_id': journal,
					'state': 'draft',
					'move_type': 'entry',
					'line_ids': line_ret,
				})
				#confirmar
				_logger.info("retornar retencion move")
				if move_obj:
					#no confirmar hasta que se confirme el pago
					#move_obj.action_post()
					return move_obj,invoice_id
				else:
					return False,False
		return False,False

	def register_retention(self,r,move_obj,invoice_id):
		ret_vals = {
			'partner_id': invoice_id.partner_id.id,
			'invoice_id':invoice_id.id,
			'journal_id':move_obj.journal_id.id,
			'seller_id':r.get("seller_id",False),
			'move_id':move_obj.id,
			'state':'draft',
			'note':r.get('note',''),
			'image':r.get('image')
		}
		rr = request.env['retention.register'].sudo().create(ret_vals)
		if rr:
			return rr
		else:
			return False


	def round_half_up(self, n, decimals=0):
		multiplier = 10 ** decimals
		return math.floor(n * multiplier + 0.5) / multiplier
