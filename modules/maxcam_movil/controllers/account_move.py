# -*- coding: utf-8 -*-
import logging
import json

from pprint import pprint
from odoo import http
from odoo.http import request
from odoo.osv import expression
from odoo import fields
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AppAccountMove(http.Controller):

    FIELDNAMES = ['id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due', 'invoice_origin', 'amount_untaxed',
                  'amount_by_group', 'amount_total', 'amount_residual', 'reception_date_client', 'state',
                  'payment_state', 'sent_to_admin']
    FIELDFILTERS = ['id', 'partner_id', 'state']

    @http.route(['/app/account_move/<int:account_move_id>/print'], type='http', methods=['GET'], auth="public",
                website=False,
                sitemap=False)
    def print_account_move(self, account_move_id, **kwargs):
        try:
            account_move = request.env['account.move'].sudo().search([('id', '=', int(account_move_id))])
        except Exception as e:
            return json.dumps({'status': 400, 'msg': str(e)})
        if account_move:
            request.uid = int(2)
            pdf, _ = request.env.ref('maxcam_account.invoice_free_form_1_id').sudo()._render_qweb_pdf([account_move.id])
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/app/account_move', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_account_move_movil(self, seller_id, limit=0, offset=0, partner_name=None, **kwargs):

        data = {'status': 200, 'msg': 'Success'}
        domain_partner = expression.AND([[('seller_id', '=', int(seller_id))]])
        
        if partner_name:
            domain_partner_name = self._get_search_domain(partner_name)
            domain_partner = expression.AND([domain_partner, domain_partner_name])
        partner = request.env['res.partner'].sudo().search(domain_partner).ids

        domain = expression.AND([[('seller_id', '=', int(seller_id)), ('partner_id', 'in', partner),
                                  ('payment_state', '!=', 'paid'), ('move_type', 'in', ['out_invoice', 'out_refund']),
                                  ('state', '=', 'posted')]])
        today = fields.date.today()
        expired_date = fields.Date.from_string(today) - relativedelta(days=90)
        domain_paid = expression.AND([[('seller_id', '=', int(seller_id)), ('partner_id', 'in', partner),
                                       ('payment_state', '=', 'paid'), ('state', '=', 'posted'),
                                       ('last_payment_date', '>', expired_date),
                                       ('move_type', 'in', ['out_invoice', 'out_refund'])]])
        for key in kwargs:
            if key in self.FIELDFILTERS:
                value = kwargs.get(key)
                domain = expression.AND([domain, [(key, '=', int(value))]])

        # Search Read
        account_move_ids = request.env['account.move'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                          limit=int(limit), offset=int(offset),
                                                                          order='create_date desc')
        account_move_ids_paid = request.env['account.move'].sudo().search_read(domain=domain_paid,
                                                                               fields=self.FIELDNAMES, limit=int(limit),
                                                                               offset=int(offset),
                                                                               order='create_date desc')

        all_acc_move_count = request.env['account.move'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                            limit=0, offset=0, order='create_date desc')
        account_move_ids = account_move_ids + account_move_ids_paid
        self.convert_field_string(account_move_ids)
        acc_move_count = len(account_move_ids) + len(account_move_ids_paid)
        all_acc_move_count = len(all_acc_move_count)
        if acc_move_count > 0:
            data.update({'data': account_move_ids, 'count': acc_move_count, 'total_count': all_acc_move_count})

        else:
            data.update({'status': 204, 'msg': 'Factura no encontrada', 'count': 0, 'data': False})

        return json.dumps(data)

    @staticmethod
    def convert_field_string(account_move):
        for record in account_move:
            record.update({'invoice_date': str(record.get('invoice_date', False)),
                           'invoice_date_due': str(record.get('invoice_date_due', False)),
                           'reception_date_client': str(record.get('reception_date_client', False))})

    @staticmethod
    def _get_search_domain(search):
        domain = []
        if search:
            for srch in search.split(" "):
                domain.append([('name', 'ilike', srch)])

        return expression.OR(domain)
