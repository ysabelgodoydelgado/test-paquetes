"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
import json
from odoo.exceptions import AccessError

from odoo import http
from odoo.addons.binaural_restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>", "/app"]


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    #@validate_token
    @http.route(_routes, type="http", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(payload)
                data = request.env[model.model].sudo().search_read(
                    domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                )
                if id:
                    domain = [("id", "=", int(id))]
                    data = request.env[model.model].sudo().search_read(
                        domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                    )
                if data:
                    _logger.info("DATA %s",data)
                    if ioc_name == 'account.move':
                        for d in data:
                            _logger.info("D %s",d)
                            if 'amount_residual' in d:
                                d.update({'amount_residual':round(d.get('amount_residual'),2)})
                    return valid_response(data)
                else:
                    return valid_response(data)
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)

    #@validate_token
    @http.route(_routes, type="http", auth="public", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload):
        import ast
        _logger.info("payload POST %s",payload)
        #payload = payload.get("payload", {})
        ioc_name = model
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        values = {}
        if model:
            try:
                
                create_uid = payload.get("create_uid",False)
                if create_uid:
                    #request.session.uid = int(create_uid)
                    request.uid = int(create_uid)
                _logger.info("PAYLOAD %s",payload)
                # changing IDs from string to int.
                for k, v in payload.items():
                    if "__api__" in k:
                        values[k[7:]] = ast.literal_eval(v)
                    else:
                        _logger.info("PARSEAR %s",v)
                        values[k] = ast.literal_eval(v)
                _logger.info("VALORES %s",values)
                resource = request.env[model.model].sudo().create(values)
                if create_uid:
                    resource.write({'create_uid':int(create_uid)})
                #return valid_response(resource.read())
            except Exception as e:
                request.env.cr.rollback()
                return invalid_response("params", str(e))
            else:
                data = resource.read()
                if resource:
                    return valid_response(data)
                else:
                    return valid_response(data)
        return invalid_response("invalid object model", "The model %s is not available in the registry." % ioc_name,)
    #@validate_token
    @http.route('/app/register_payment_approval', type="json", auth="public", methods=["POST"], csrf=False)
    def post_json(self, model=None, id=None, **payload):
        import ast
        _logger.info("payload POST JSON %s",payload)
        ioc_name = 'payment.approval'
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        values = {}
        if model:
            try:
                create_uid = payload.get("create_uid",False)
                if create_uid:
                    #request.session.uid = int(create_uid)
                    request.uid = int(create_uid)
                _logger.info("PAYLOAD %s",payload)
                # changing IDs from string to int.
                for k, v in payload.items():
                    if "__api__" in k:
                        values[k[7:]] = ast.literal_eval(v)
                    else:
                        _logger.info("PARSEAR %s",v)
                        values[k] = ast.literal_eval(v)
                _logger.info("VALORES %s",values)
                resource = request.env[model.model].sudo().create(values)
                if create_uid:
                    resource.write({'create_uid':int(create_uid)})
                #return valid_response(resource)
            except Exception as e:
                request.env.cr.rollback()
                _logger.info(str(e))
                return invalid_response("params", e)
            else:
                data = resource.read()
                if resource:
                    return valid_response(data)
                else:
                    return valid_response(data)
        return invalid_response("invalid object model", "The model %s is not available in the registry." % ioc_name,)

    #@validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        #payload = payload.get('payload', {})
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        values = {}
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            for k, v in payload.items():
                if "__api__" in k:
                    values[k[7:]] = ast.literal_eval(v)
                else:
                    _logger.info("PARSEAR %s",v)
                    values[k] = ast.literal_eval(v)
            create_uid = payload.get("create_uid",False)
            if create_uid:
                #request.session.uid = int(create_uid)
                request.uid = int(create_uid)
            record.write(values)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e)
        else:
            return valid_response(record.read())

    #@validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404,)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    #@validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        #payload = payload.get('payload')
        action = action if action else payload.get('_method')
        args = []
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            if record and _callable:
                # action is a dynamic variable.
                getattr(record, action)(*args) if args else getattr(record, action)() 
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found or %s object has no method %s" % (_id, model, action),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response("record %s has been successfully update" % record.id)
    
class APIControllerVersions(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    @http.route('/app/versions', type="http", auth="public", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, **payload):
        android_version = request.env['ir.config_parameter'].sudo().get_param('android_version')
        ios_version = request.env['ir.config_parameter'].sudo().get_param('ios_version')
        data = {
            "android_version": android_version,
            "ios_version": ios_version
        }
        response = {
            "data": data,
            "status": 200
        }
        return json.dumps(response)