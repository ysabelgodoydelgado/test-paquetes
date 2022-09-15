# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class MaxcamAccountPaymentInh(models.Model):
	_inherit = 'account.payment'

	attachment_id = fields.Many2one('ir.attachment', string='Attachment', ondelete='cascade',
									domain=[('res_model', '=', 'account.payment')])
	foreign_payment_currency_id = fields.Many2one('res.currency', string="Moneda/Divisa",
												  default=lambda self: self.env.ref("base.VEF"))
	foreign_payment_currency_rate = fields.Float(string='Tasa Divisa', digits=(12, 2),
												 default=lambda self: self.compute_foreign_rate_payment(),
												 help='Guarda la tasa en que se calcula el total en la moneda foránea')

	def get_last_rate_payment(self, rate_ids, date_invoice=False):
		domain_rate = [('id', 'in', rate_ids)]
		if date_invoice:
			domain_date = [('name', '=', date_invoice)]
			domain = domain_rate + domain_date
			rate = self.env['res.currency.rate'].sudo().search(domain, order='write_date desc', limit=1)
			if not rate:
				rate = self.env['res.currency.rate'].sudo().search(domain_rate, order='name desc, write_date desc',
																   limit=1)
		else:
			rate = self.env['res.currency.rate'].sudo().search(domain_rate,
															   order='name desc, write_date desc', limit=1)
		return rate

	@api.onchange('partner_id')
	def compute_foreign_rate_payment(self):
		for record in self:
			rate_ids = record.foreign_payment_currency_id.rate_ids.ids if record.foreign_payment_currency_id else False
			if rate_ids and not record.foreign_payment_currency_rate:
				rate = record.get_last_rate_payment(rate_ids, record.date)
				if len(rate) > 0:
					record.foreign_payment_currency_rate = round(rate.rate, 4)
	
	@api.onchange('journal_id')
	def _onchange_journal_maxcam(self):
		_logger.info("Trigger onchange journal_id account PAYMENT")
		#si es banco o efectivo enviar siempre / en el name
		if self.journal_id and self.journal_id.type in ['cash','bank']:
			self.name = '/'

class MaxcamAccountPaymentRegisterInh(models.TransientModel):
	_inherit = 'account.payment.register'

	foreign_payment_currency_id = fields.Many2one('res.currency', string="Moneda / Divisa",
												  default=lambda self: self.env.ref("base.VEF"))
	foreign_payment_currency_rate = fields.Float(string='Divisa', digits=(12, 2),
												 default=lambda self: self.compute_foreign_rate_payment(),
												 help='Guarda la tasa en que se calcula el total en la moneda foránea')

	def get_last_rate_payment(self, rate_ids, date_invoice=False):
		domain_rate = [('id', 'in', rate_ids)]
		if date_invoice:
			domain_date = [('name', '=', date_invoice)]
			domain = domain_rate + domain_date
			rate = self.env['res.currency.rate'].sudo().search(domain, order='write_date desc', limit=1)
			if not rate:
				rate = self.env['res.currency.rate'].sudo().search(domain_rate, order='name desc, write_date desc',
																   limit=1)
		else:
			rate = self.env['res.currency.rate'].sudo().search(domain_rate,
															   order='name desc, write_date desc', limit=1)
		return rate

	@api.onchange('partner_id')
	def compute_foreign_rate_payment(self):
		for record in self:
			rate_ids = record.foreign_payment_currency_id.rate_ids.ids if record.foreign_payment_currency_id else False
			if rate_ids and not record.foreign_payment_currency_rate:
				rate = record.get_last_rate_payment(rate_ids, record.payment_date)
				if len(rate) > 0:
					record.foreign_payment_currency_rate = round(rate.rate, 4)

	def _create_payment_vals_from_wizard(self):
		payment_vals = {
			'date': self.payment_date,
			'amount': self.amount,
			'payment_type': self.payment_type,
			'partner_type': self.partner_type,
			'ref': self.communication,
			'journal_id': self.journal_id.id,
			'currency_id': self.currency_id.id,
			'partner_id': self.partner_id.id,
			'partner_bank_id': self.partner_bank_id.id,
			'payment_method_id': self.payment_method_id.id,
			'destination_account_id': self.line_ids[0].account_id.id,
			'foreign_payment_currency_id': self.foreign_payment_currency_id.id,
			'foreign_payment_currency_rate': self.foreign_payment_currency_rate,

		}

		if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
			payment_vals['write_off_line_vals'] = {
				'name': self.writeoff_label,
				'amount': self.payment_difference,
				'account_id': self.writeoff_account_id.id,
			}
		return payment_vals
