# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettingsMaxcam(models.TransientModel):
    _inherit = 'res.config.settings'

    overdraw_inventory = fields.Boolean('Don t overdraw inventory',
                                        help='Don t overdraw inventory when selling products')

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsMaxcam, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            overdraw_inventory=get_param('overdraw_inventory', default=False),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('overdraw_inventory', self.overdraw_inventory)

        super(ResConfigSettingsMaxcam, self).set_values()
