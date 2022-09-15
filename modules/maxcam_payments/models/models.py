# -*- coding: utf-8 -*-

from odoo import models, fields, api

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict
class HrEmployeeMaxcamPayments(models.Model):
	_inherit = 'hr.employee'

	journal_id_maxcam = fields.Many2one('account.journal', string='Diario Asociado', tracking=1,domain="[('type', '=','cash')]")

class AccountTaxMaxcamPayments(models.Model):
	_inherit = 'account.tax'
	in_app = fields.Boolean(string='En app')

class AccountMoveMaxcamPaymentsApproval(models.Model):
	_inherit = 'account.move'
	approval_line_id = fields.Many2one('payment.approval.line', string='Linea de Recibo de pago Maxcam')

	#funcion para buscar saldo a favor del cliente
	def _compute_payments_partner_maxcam(self,partner_id):
		balance = 0
		_logger.info("partner recibido a buscar balance %s",partner_id)
		move = self
		try:
			pay_term_lines = self.env['account.account'].sudo().search([('user_type_id.type','in',('receivable', 'payable'))]).ids
			domain = [
				('account_id', 'in', pay_term_lines),
				('move_id.state', '=', 'posted'),
				('partner_id', '=', int(partner_id)),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]
			#es cliente
			domain.append(('balance', '<', 0.0))
			
			_logger.info("buscar con el domain %s",domain)
			for line in self.env['account.move.line'].search(domain):
				_logger.info("adentro de linea %s",line)
				amount = abs(line.amount_residual_currency)
				_logger.info("AMOUNT %s",amount)
				balance += amount
		except Exception as e:
			_logger.info("ERROR BUSCANDO BALANCE %s",str(e))
		return balance


	def js_assign_outstanding_line_maxcam(self, line_id,inv_id):
		''' Called by the 'payment' widget to reconcile a suggested journal item to the present
		invoice.

		:param line_id: The id of the line to reconcile with the current invoice.
		'''
		#self.ensure_one()
		lines = self.env['account.move.line'].sudo().browse(line_id)
		inv = self.env['account.move'].sudo().browse(inv_id)
		if len(lines)>o and inv:
			lines += inv.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
			return lines.reconcile()
		else:
			return False
 
	#funcion para buscar saldo a favor del cliente
	def _compute_payments_partner_maxcam_lines(self,partner_id,amount_to_cover):
		_logger.info("partner en linea de pagos %s",partner_id)
		move = self
		lines_moves = []
		balance = 0
		try:
			pay_term_lines = self.env['account.account'].sudo().search([('user_type_id.type','in',('receivable', 'payable'))]).ids
			domain = [
				('account_id', 'in', pay_term_lines),
				('move_id.state', '=', 'posted'),
				('partner_id', '=', int(partner_id)),
				
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]
			#es cliente
			domain.append(('balance', '<', 0.0))
			_logger.info("buscar con el domain %s",domain)
			for line in self.env['account.move.line'].search(domain):
				_logger.info("adentro de linea %s",line)
				amount = abs(line.amount_residual_currency)
				_logger.info("AMOUNT %s",amount)
				balance += amount
				#si el monto acumulado de los pagos recorridos es mayor o igual al que necesito cubrir entonces no busco mas
				lines_moves.append(line.id)
				if balance >= amount_to_cover:
					break
			return lines_moves

		except Exception as e:
			_logger.info("ERROR BUSCANDO linea de pagos que cubran el monto %s",str(e))
			return lines_moves