# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class Client(models.Model):
    _inherit = 'res.partner'

    @api.onchange('vat', 'prefix_vat')
    def onchange_validate_vat_longitude(self):
        if self.vat and self.prefix_vat == 'j':
            min_len = int(self.env['ir.config_parameter'].sudo().get_param('vat_longitude', default=9))
            if len(self.vat) > min_len:
                self.vat = self.vat[0:min_len]

    business_name = fields.Char(string='Razón Social', required=True)
    prefix_vat = fields.Selection([
        ('v', 'V'),
        ('e', 'E'),
        ('j', 'J'),
        ('g', 'G'),
        ('c', 'C'),
    ], 'Prefijo Rif', required=True, default='v')
    vat = fields.Char(string='RIF', help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.", required=True)
    #city = fields.Many2one('master.city', 'Ciudad', domain="[('state','=','active')]")
    phone = fields.Char(required=False)

    @api.constrains('vat', 'prefix_vat')
    def _check_longitude_vat(self):
        for p in self:
            min_len = int(self.env['ir.config_parameter'].sudo().get_param('vat_longitude', default=9))
            if p.vat and p.prefix_vat:
                if len(p.vat) < min_len and p.prefix_vat == 'j':
                    raise exceptions.ValidationError("Por favor verifica si el RIF posee la longitud correcta")
