# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DepositPayment(models.Model):
	_name = 'deposit.payment'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'maxcam Deposit Payments'
	_order = 'create_date desc'

	name = fields.Char(string="Referencia", tracking=True)
	date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)
	currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string="Moneda",
								  default=lambda x: x.env.company.currency_id)
	amount = fields.Monetary(string="Monto", currency_field='currency_id', tracking=True,required=True)
	invoice_ids = fields.Many2many('account.move', string="Facturas", tracking=True)
	payment_ids = fields.Many2many('account.payment',)
	partner_id = fields.Many2one('res.partner', string="Cliente", tracking=True)
	attachment_ids = fields.Many2many('ir.attachment', 'deposit_payment_id', 'attachment_id', string="Adjunto",
									  help="If any")
	seller_id_user = fields.Many2one('res.users', string='Vendedor', tracking=True,required=False)
	seller_id = fields.Many2one('hr.employee', string='Vendedor', tracking=True,required=True)
	journal_id = fields.Many2one('account.journal', string="Diario", help="Diario",required=True)

	state = fields.Selection([
		('draft', 'Borrador'),
		('confirmed', 'Confirmado'),
		('done', 'Conciliado'),
		('cancel', 'Cancelado'),
	], string='Estatus', copy=False, index=True, tracking=True,default="draft")

	move_id = fields.Many2one('account.move', string='Asiento Contable')
	payment_approval_ids = fields.One2many('payment.approval', 'deposit_id', string='Recibos Asociados')
	payment_approval_lines_ids = fields.One2many('payment.approval.line', 'deposit_id', string='Recibos Asociados')

	def cancel_deposit(self):
		if self.move_id:
			self.move_id.button_draft()
			self.move_id.button_cancel()
		self.write({"payment_approval_lines_ids":[(5)],'state':'cancel'})


	@api.onchange('seller_id')
	def _onchange_seller_id(self):
		approvals = []
		#all_approval = self.env['payment.approval'].sudo().search([('seller_id','=',self.seller_id.id),('state','=','process'),('deposit_id','=',False)])
		#ojo con depositos asociados pero no confirmados
		#cash_conciled es si esa linea de efectivo fue conciliada: definir si concialiada es a nivel bancario
		#for ap in all_approval:
		#	if any(line.journal_id.type == 'cash' and not line.cash_conciled for line in ap.payment_approval_line):
		#		approvals.append(ap.id)
		_logger.info("SELLER EN ONCHANGE PARA BUSCAR LINEAS %s",self.seller_id)
		all_lines = self.env['payment.approval.line'].sudo().search([('payment_approval.seller_id','=',self.seller_id.id),('payment_approval.state','=','process'),('deposit_id','=',False),('journal_id.type','=','cash')]).ids
		return {
			'domain': {
				'payment_approval_lines_ids': [('id', 'in', all_lines)]
				#'payment_approval_ids': [('id', 'in', approvals)]
			}
		}
	"""@api.onchange('payment_approval_ids')
	def _onchange_approvals(self):
		_logger.info("disparo el onchangeeeeeeeee de ordenes asociadas %s",self.payment_approval_ids)
		ids_approvals = self.payment_approval_ids._origin.ids
		_logger.info("ids_approvals %s",ids_approvals)

		origenes_en_lineas = self.invoice_ids.mapped('approval_line_id')
		origenes_ids = origenes_en_lineas.mapped('payment_approval').ids

		_logger.info("origenes_ids %s",origenes_ids)

		
		result = list(set(origenes_ids).symmetric_difference(set(ids_approvals)))
		_logger.info("RESULTA %s",result)
		
		_logger.info("ids_diff %s",result)
		if len(origenes_en_lineas) > len(self.payment_approval_ids):
			_logger.info("elimino una orden, hay que eliminar lineas (facturas) %s",result)
			for i in result:
				lineas_a_eliminar = self.invoice_ids.filtered(lambda r: r.approval_line_id.payment_approval.id == i)
				for l in lineas_a_eliminar:
					self.write({'invoice_ids':[(3, l.id)]}) 
				#lineas_a_eliminar.unlink()
				#self._amount_all()
		elif len(origenes_en_lineas) < (len(self.payment_approval_ids)):
			docs = []
			for i in result:
				orden = self.env['payment.approval'].browse(i)
				if orden:
					for line in orden.payment_approval_line.filtered_domain([('journal_id.type','=','cash')]):
						docs.append((4,line.invoice_id.id))
				if len(docs) > 0:
					self.write({'invoice_ids':docs})
			_logger.info("los origenes son menores asi que debo agregar una nueva %s",result)
		else:
			pass"""
	#hacer que al elegir un recibo de pago se llene solo la linea y pagos OJO puede que no sea necesario pagos

	def processs_deposit(self):
		_logger.info("mandar a hacer el procesar del deposito")
		deposit_account = self.env['ir.config_parameter'].sudo().get_param('maxcam_seller_account')
		#por el haber
		_logger.info("esta es la cuenta configurada para deposito de vendedores %s",deposit_account)
		#seller_employee = self.env['hr.employee'].sudo().search([('user_id','=',int(self.seller_id.id))])
		#seller_journal = False
		#if seller_employee:
		seller_journal = self.seller_id.journal_id_maxcam

		if not seller_journal:
			raise UserError("Diario de efectivo en vendedor es obligatorio")
		#payment_debit_account_id por el debe
		_logger.info("Cuenta de recibo pendiente del diario del vendedor %s",seller_journal.payment_debit_account_id)
		#if not deposit_account:
		#	raise UserError("La cuenta contable de deposito es obligatoria")
		if not self.journal_id:
			raise UserError("El diario es obligatorio")
		if self.amount <=0:
			raise UserError("No puedes procesar montos menores a 0")
		line_ret = []
		line_ret.append((0, 0, {
			'name': self.name,
			'account_id': self.journal_id.payment_debit_account_id.id,#int(deposit_account),
			#'partner_id': self.partner_id.id,
			'debit': self.amount,
			'credit': 0,
			#'move_id': move_id
		}))
		line_ret.append((0, 0, {
			'name': self.name,
			'account_id': seller_journal.payment_debit_account_id.id,
			
			#'partner_id': self.partner_id.id,
			'debit': 0,
			'credit': self.amount,
			#'move_id': move_id
		}))

		# Asiento Contable
	 
		move_obj = self.env['account.move'].create({
			#'name': self.name,
			'date': self.date,
			'journal_id': self.journal_id.id,
			'state': 'draft',
			'move_type': 'entry',
			'line_ids': line_ret,
			'ref':self.name,
		})
		_logger.info("move_obj creado %s",move_obj)
		move_obj.action_post()
		self.write({"move_id":move_obj.id,"state":"confirmed"})
		return True
		#return move_obj

	def make_done(self,involved_lines=False):
		for i in self:
			#maxcam esta validando el deposito
			for line in i.payment_approval_lines_ids:
				#ya esta pagada, cambiar fecha de ultimo pago por la del deposito en caso de efectivo
				if line.invoice_id and line.invoice_id.amount_residual == 0:
					_logger.info("a la factura %s",line.invoice_id)
					_logger.info("la fecha: %s",i.date)
					line.invoice_id.sudo().write({
						'cash_reconcile_date':i.date
					})
				line.payment_related.write({'is_matched':True})
				line.write({"cash_conciled":True})
			i.write({'state':'done'})

	def remove_done(self):
		for i in self:
			for line in i.payment_approval_lines_ids:
				if line.invoice_id and line.invoice_id.amount_residual == 0:
					_logger.info("a la factura %s",line.invoice_id)
					_logger.info("la fecha: %s",i.date)
					line.invoice_id.sudo().write({
						'cash_reconcile_date':False
					})
				line.payment_related.write({'is_matched':False})
				line.write({"cash_conciled":False})
			i.write({'state':'confirmed'})

class MaxcamDepositApprovalInh(models.Model):
	_inherit = 'payment.approval'

	deposit_id = fields.Many2one('deposit.payment', string='Deposito Efectivo Asociado', tracking=1)


class MaxcamDepositApprovalLineInh(models.Model):
	_inherit = 'payment.approval.line'

	deposit_id = fields.Many2one('deposit.payment', string='Deposito Efectivo Asociado', tracking=1)


