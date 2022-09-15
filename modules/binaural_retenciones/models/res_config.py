# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vat_id = fields.Integer(string="Longitud de RIF", required=True, default=9)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['vat_id'] = int(
            self.env['ir.config_parameter'].sudo().get_param('vat_longitude', default=9))
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('vat_longitude', self.vat_id)
        super(ResConfigSettings, self).set_values()
