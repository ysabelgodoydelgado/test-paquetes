# -*- coding: utf-8 -*-

import logging
from odoo import http, tools
from odoo.http import request
from odoo.addons.web.controllers.main import Session

_logger = logging.getLogger(__name__)


class SessionInh(Session):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        res = super(SessionInh, self).authenticate(db, login, password, base_location)
        if res:
            rh_user = request.env['hr.employee'].sudo().search([('user_id', '=', res.get('user_id')[0])], limit=1)
            if rh_user:
                res.setdefault('activate_payment_app', rh_user.activate_payment_app)
            else:
                res.setdefault('activate_payment_app', False)
        return res
