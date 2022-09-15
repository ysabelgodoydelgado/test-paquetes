# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json

from odoo import http
from odoo.http import request
from odoo.osv import expression
from werkzeug import urls
from pprint import pprint
_logger = logging.getLogger(__name__)


class AppPriceList(http.Controller):

    APPSTATE = {200: 'Succes', 400: 'Listado de precios no dispolibre o sin formula de calculo',
                409: 'La solicitud no se pudo completar debido a un conflicto del recurso'}

    @http.route('/app/product_pricelist', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_pricelist_movil(self, product_id, partner_id):
        data = {'status': 200, 'msg': self.APPSTATE[200]}
        price = 0
        if type(int(partner_id)) == int and type(int(product_id)) == int:
            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            pricelist = partner.property_product_pricelist
            product = request.env['product.template'].sudo().browse(int(product_id))
            if pricelist.active:
                price = pricelist.price_get(product.id, 1, partner)
                price = price.get(list(price.keys())[0])
            data.update({'data': price})
        else:
            data.update({'status': 409, 'msg': self.APPSTATE[409]})
        return json.dumps(data)
