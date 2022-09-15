# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettingsVersions(models.TransientModel):
    _inherit = 'res.config.settings'

    android_version = fields.Char(string="Version de Android", required=True)
    ios_version = fields.Char(string="Version de iOS", required=True)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsVersions, self).get_values()
        res['android_version'] = self.env['ir.config_parameter'].sudo().get_param('android_version')
        res['ios_version'] = self.env['ir.config_parameter'].sudo().get_param('ios_version')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('android_version', self.android_version)
        self.env['ir.config_parameter'].sudo().set_param('ios_version', self.ios_version)
        super(ResConfigSettingsVersions, self).set_values()
