# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json

from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AppResPartner(http.Controller):

    FIELDNAMES = ['id', 'name']
    FIELDFILTERS = ['user_id']

    @http.route('/app/hr_employee', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
    def app_hr_employee_movil(self, limit=20, offset=0, **kwargs):
        data = {'status': 200, 'msg': 'Success'}
        domain = expression.AND([[('active', '=', True)]])
        for key in kwargs:
            if key in self.FIELDFILTERS:
                value = kwargs.get(key)
                domain = expression.AND([domain, [(key, '=', int(value))]])

        # Search Read
        employee_ids = request.env['hr.employee'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
                                                                     limit=int(limit), offset=int(offset),
                                                                     order='name asc')
        all_employee_count = request.env['hr.employee'].sudo().search_count(domain)
        employee_count = len(employee_ids)
        if employee_count > 0:
            data.update({'data': employee_ids, 'count': employee_count, 'total_count': all_employee_count})
        else:
            data.update({'status': 204, 'msg': 'Empleado no Registrado', 'count': 0, 'data': False})
        return json.dumps(data)
