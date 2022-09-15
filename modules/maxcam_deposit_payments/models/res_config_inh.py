# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettingsMaxcamPayments(models.TransientModel):
	_inherit = 'res.config.settings'

	maxcam_seller_account = fields.Many2one(
		comodel_name='account.account',
		string="Cuenta para deposito de vendedores",
		readonly=False,
		domain=[('deprecated', '=', False)])

	def set_values(self):
		super(ResConfigSettingsMaxcamPayments, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('maxcam_seller_account', self.maxcam_seller_account.id)

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsMaxcamPayments, self).get_values()
		ac = self.env['ir.config_parameter'].sudo().get_param('maxcam_seller_account')
		if ac:
			res['maxcam_seller_account'] = int(ac)
		return res