# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json

from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AppResPartner(http.Controller):

    FIELDNAMES = ['id', 'name', 'credit_limit', 'total_due', 'street', 'street2', 'city', 'state_id', 'zip', 'seller_id',
                  'country_id', 'child_ids', 'property_product_pricelist', 'property_payment_term_id', 'type', 'active',
                  'seller_id', 'property_payment_term_id']
    FIELDFILTERS = ['id', 'name', 'seller_id']

    @http.route('/app/res_partner', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_res_partner_movil(self, limit=20, offset=0, **kwargs):
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
        partner_ids = request.env['res.partner'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                    limit=int(limit), offset=int(offset),
                                                                    order='name asc')
        all_partner_count = request.env['res.partner'].sudo().search_count(domain)
        partner_count = len(partner_ids)
        if partner_count > 0:
            # Get child_ids
            self._get_partner_child(partner_ids)
            data.update({'data': partner_ids, 'count': partner_count, 'total_count': all_partner_count})
        else:
            data.update({'status': 204, 'msg': 'Cliente no encontrado', 'count': 0, 'data': False})
        return json.dumps(data)

    @staticmethod
    def _get_search_domain(search):
        domain = []
        if search:
            for srch in search.split(" "):
                domain.append([('name', 'ilike', srch)])

        return expression.OR(domain)

    def _get_partner_child(self, partner_ids):
        """
        Busca los datos de la direccion de los clientes
        :param partner_ids: res.parnert ( json )
        :return: no es necesario porque el parametro es por valor
        """
        for partner in partner_ids:
            child_ids = partner.get('child_ids', False)
            if child_ids:
                res_child_ids = request.env['res.partner'].sudo().search_read(domain=[('id', 'in', child_ids)],
                                                                              fields=self.FIELDNAMES, order='name asc')
                partner.update({'child_ids': res_child_ids})

