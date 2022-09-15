"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
from odoo.exceptions import AccessError

from odoo import http
from odoo.addons.binaural_restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)

"""def validate_access_seller(func):
   

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
       
        _logger.info("VALIDATE ACESS %s",kwargs)
        sale_order = kwargs.get('sale_order',{})
        create_uid = sale_order.get('user_id',False)
        if create_uid:
            employee = request.env['hr.employee'].sudo().search([('user_id','=',int(create_uid))],limit=1)
            _logger.info("EMPLOYE %s",employee)
            _logger.info("employee.cannot_access_app %s",employee.cannot_access_app)
            if employee and employee.cannot_access_app:
                _logger.info("bloqueado")
                #raise AccessError("ALFRESITA")
                return {'status': 401, 'msg': 'No tienes acceso a esta funcionalidad'}
            else:
                return func(self, *args, **kwargs)
        else:
            return func(self, *args, **kwargs)
    return wrap"""


def check_access(uid):
    if uid:
        employee = request.env['hr.employee'].sudo().search([('user_id','=',int(uid))],limit=1)
        if employee and employee.cannot_access_app:
            return False,'No tienes acceso a esta funcionalidad'
    return True,''
