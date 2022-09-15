# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json

from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AppProductBrand(http.Controller):

    FIELDNAMES = ['id', 'name', 'active']
    FIELDFILTERS = ['id', 'name']

    @http.route('/app/product_brand', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_product_brand_movil(self, limit=20, offset=0, **kwargs):
        data = {'status': 200, 'msg': 'Success'}
        domain = expression.AND([[('active', '=', True)]])
        for key in kwargs:
            if key in self.FIELDFILTERS:
                if key == 'name':
                    search_domain = self._get_search_domain(kwargs.get(key))
                    domain = expression.AND([domain, search_domain])
                else:
                    value = kwargs.get(key)
                    domain = expression.AND([domain, [(key, '=', int(value))]])

        # Search Read
        brand_ids = request.env['product.brand'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                    limit=int(limit), offset=int(offset),
                                                                    order='name asc')
        all_brand_count = request.env['product.brand'].sudo().search_count(domain)
        brand_count = len(brand_ids)
        if brand_count > 0:
            data.update({'data': brand_ids, 'count': brand_count, 'total_count': all_brand_count})
        else:
            data.update({'status': 204, 'msg': 'No hay marcas de productos', 'count': 0, 'data': False})

        return json.dumps(data)

    @staticmethod
    def _get_search_domain(search):
        domain = []
        if search:
            for srch in search.split(" "):
                domain.append([('name', 'ilike', srch.capitalize())])

        return expression.OR(domain)
