 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json

from odoo import http
from odoo.http import request
from odoo.osv import expression
from werkzeug import urls
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)

from odoo.addons.maxcam_movil.controllers.functions import check_access
class AppStock(http.Controller):

	FIELDNAMES = ['id', 'name', 'qty_available', 'list_price', 'default_code', 'barcode', 'alternate_code', 'brand_id',
				  'sales_policy', 'available_qty', 'quantity_package']
	FIELDFILTERS = ['id', 'name', 'brand_id', 'available_qty']
	#@validate_access_seller
	@http.route('/app/product_template', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_stock_movil(self, limit=0, offset=0,uid=False, **kwargs):
		data = {'status': 200, 'msg': 'Success'}
		domain = expression.AND([[('active', '=', True), ('sale_ok', '=', True)]])
		for key in kwargs:
			if key in self.FIELDFILTERS:
				if key == 'name':
					search_domain = self._get_search_domain(kwargs.get(key))
					domain = expression.AND([domain, search_domain])
				elif key == 'available_qty':
					
					value = kwargs.get(key)
					key = 'available_qty_store'
					domain = expression.AND([domain, [(key, '>', int(value))]])
				else:
					value = kwargs.get(key)
					domain = expression.AND([domain, [(key, '=', int(value))]])

		# Search Read
		product_ids = request.env['product.template'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
																		 limit=int(limit), offset=int(offset),
																		 order='name asc')

		#/app/product_template?partner_id=9674&name=A&available_qty=0
		all_product_count = request.env['product.template'].sudo().search_count(domain)
		product_count = len(product_ids)
		if product_count > 0:
			# get id product.product
			self.get_id_product_product(product_ids)
			# get url image
			self.get_url_image_product(product_ids)
			data.update({'data': product_ids, 'count': product_count, 'total_count': all_product_count})
		else:
			data.update({'status': 204, 'msg': 'No hay productos', 'count': 0, 'data': False})
		
		if uid:
			can_access,msg = check_access(uid)
			if not can_access:
				#data = {'status': 401, 'msg': msg}
				data.update({'status': 401, 'msg': msg, 'count': 0, 'data': False})
		return json.dumps(data)

	@staticmethod
	def get_id_product_product(product_ids):
		for product in product_ids:
			p_id = product.get('id')
			p_ids = request.env['product.product'].sudo().search([('product_tmpl_id', '=', p_id)], limit=1).id
			product.update({'product_id': p_ids})

	@staticmethod
	def get_url_image_product(product_ids):
		"""
		Concatena la url para la image de cada producto
		:param product_ids: json (product.template)
		:return: no es necesario porque el parametro es por valor
		"""
		webbase_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		for record in product_ids:
			product_id = str(record.get('id'))
			url_img = "/web/image?model=product.template&id=" + product_id + "&field=image_1024"
			url_complete = urls.url_join(webbase_url, url_img)
			record.update({'image': url_complete})

	@staticmethod
	def _get_search_domain(search):
		domain = []
		if search:
			if search[0] == '%' or search[-1] == '%':
				domain.append(['|',('name', '=ilike', search),('alternate_code','=ilike',search)])
			else:
				domain.append(['|',('name', 'ilike', search),('alternate_code','ilike',search)])

		return expression.OR(domain)
