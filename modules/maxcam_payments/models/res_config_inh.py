# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettingsMaxcamPaymentsMaxcam(models.TransientModel):
	_inherit = 'res.config.settings'

	journal_retention_client_maxcam = fields.Many2one(
		comodel_name='account.journal',
		string="Diario de retenciones",
		readonly=False)

	def set_values(self):
		super(ResConfigSettingsMaxcamPaymentsMaxcam, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('journal_retention_client_maxcam', self.journal_retention_client_maxcam.id)

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsMaxcamPaymentsMaxcam, self).get_values()
		ac = self.env['ir.config_parameter'].sudo().get_param('journal_retention_client_maxcam')
		if ac:
			res['journal_retention_client_maxcam'] = int(ac)
		return res