# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class WizardMessageMaxcamUpdateCost(models.TransientModel):
	_name = "wizard.message.maxcam.update.cost"
	_description = "Mensaje Confirmacion"

	name_modal_purchase_partial = fields.Char(string='Mensaje')
	purchase_id = fields.Many2one('purchase.order', string='Orden')

	def button_confirm_cost(self):
		for record in self:
			record.purchase_id.write({
				'confirmed_update_cost': True,
                'wizard_confirm':True,
			})
			record.purchase_id.button_confirm()

	def button_reject_update_cost(self):
		for record in self:
			record.purchase_id.write({
				'confirmed_update_cost': False,
                'wizard_confirm':True,
			})
			record.purchase_id.button_confirm()