# -*- coding: utf-8 -*-
import logging
import json

from pprint import pprint
from odoo import http, fields
from odoo.http import request
from odoo.osv import expression
import base64
_logger = logging.getLogger(__name__)


class AppAccountPayment(http.Controller):

    FIELDNAMES = ['id', 'name', 'journal_id', 'amount', 'date', 'ref', 'partner_id', 'state']
    FIELDFILTERS = ['id', 'partner_id', 'journal_id']

    @http.route('/app/register_payment', type='json', methods=['POST'], auth='public', website=False, sitemap=False)
    def app_account_payment_register_movil(self, user_id, image=False, **kwargs):
        data = {'status': 200, 'msg': 'Success'}
        invoice_id = kwargs.get('invoice_id', False)
        amount = kwargs.get('amount', False)
        currency_id = kwargs.get('currency_id', False)
        journal_id = kwargs.get('journal_id', False)
        if invoice_id and amount and currency_id and journal_id and user_id:
            invoice = request.env['account.move'].sudo().search([('id', '=', int(invoice_id))])
            # Create a payment at rate 1:2.
            ctx = {'active_model': 'account.move', 'active_ids': invoice.ids}
            try:
                payment_register = request.env['account.payment.register'].sudo().with_context(**ctx).create({
                    'amount': float(amount),
                    'currency_id': int(currency_id),
                    'journal_id': int(journal_id),
                    #'payment_date': kwargs.get('date', fields.Date.today()),
                    'communication': kwargs.get('ref', invoice.name),
                    'cheque_amount': float(amount),
                })
                payment_vals = payment_register._create_payment_vals_from_wizard()
                """if image:
                    att1 = base64.b64encode(image.get('content'))
                    _logger.info("ATT1 %s",att1)
                    #att1 = self._set_image_value(image)
                    #payment_vals.update({'attachment_id': att1})
                    payment_vals.update({'capture':att1})"""
                payment_vals.update({'company_id': 1, 'payment_type': 'inbound', 'user_id': user_id,
                                     'payment_method_id': request.env.ref('account.account_payment_method_manual_in').id,
                                     })

                payment = request.env['account.payment'].sudo().create(payment_vals)
                payment.action_post()
            except Exception as e:
                _logger.error("Error al Registrar el pago %s", e)
                data.update({'status': 400, 'msg': e})
        else:
            data.update({'status': 400, 'msg': 'Faltan parametros de registro'})
        return json.dumps(data)

    @http.route('/app/account_payment', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_account_payment_movil(self, seller_id, limit=20, offset=0, partner_name=None, **kwargs):
        data = {'status': 200, 'msg': 'Success'}
        domain = []
        domain_partner = expression.AND([[('seller_id', '=', int(seller_id))]])
        if partner_name:
            domain_partner_name = self._get_search_domain(partner_name)
            domain_partner = expression.AND([domain_partner, domain_partner_name])
        partner = request.env['res.partner'].sudo().search(domain_partner).ids

        domain = expression.AND([[('partner_id', 'in', partner)]])
        for key in kwargs:
            if key in self.FIELDFILTERS:
                value = kwargs.get(key)
                domain = expression.AND([domain, [(key, '=', value)]])

        # Search Read
        payment_ids = request.env['account.payment'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                        limit=int(limit), offset=int(offset),
                                                                        order='create_date desc')
        all_payment_count = request.env['account.payment'].sudo().search_count(domain)
        payment_count = len(payment_ids)
        if payment_count > 0:
            self.convert_field_string(payment_ids)
            data.update({'data': payment_ids, 'count': payment_count, 'total_count': all_payment_count})

        else:
            data.update({'status': 204, 'msg': 'pago no encontrado', 'count': 0, 'data': False})

        return json.dumps(data)

    def _set_image_value(self, post_value):
        """
        registro de imagen
        :param post_value:imagen
        :return: objeto imagen (ir.attachment)
        """
        file_name = post_value.filename.lower()
        attachment_value = {
            'name': file_name,
            'res_name': file_name,
            'res_model': 'account.payment',
            'res_id': request.env.user.partner_id,
            'datas': post_value.read(),
        }
        att1 = attachment_value
        att1['res_field'] = post_value.content_type
        try:
            att1 = request.env['ir.attachment'].sudo().create(att1)
        except Exception as e:
            _logger.error("Error al cargar imagen %s", e)
        return att1.id

    @staticmethod
    def convert_field_string(account_move):
        for record in account_move:
            record.update({'date': str(record.get('date', False))})

    @staticmethod
    def _get_search_domain(search):
        domain = []
        if search:
            for srch in search.split(" "):
                domain.append([('name', 'ilike', srch)])

        return expression.OR(domain)
