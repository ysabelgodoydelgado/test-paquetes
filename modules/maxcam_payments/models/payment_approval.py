# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict

import pytz
MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'out_receipt': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
	'in_receipt': 'supplier',
}
class PaymentApproval(models.Model):
	_name = 'payment.approval'
	_description = 'Payment Approval'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	#_order = 'name'
	_rec_name = 'partner_id'
	_order = 'create_date desc'

	_check_company_auto = True

	name = fields.Char(string="Nombre",tracking=True)
	partner_id = fields.Many2one('res.partner', 'Cliente', help="Cliente",tracking=True,required=True)
	amount = fields.Float(string="Monto", help="Monto",tracking=True)
	amount_compute = fields.Float(string='Monto calculado')
	journal_id = fields.Many2one('account.journal', string="Diario", help="Diario")
	payment_approval_line = fields.One2many('payment.approval.line', 'payment_approval',tracking=True)
	payment_approval_methods = fields.One2many('payment.approval.methods', 'payment_approval', string='Metodos de pago')
	state = fields.Selection([
		('draft', 'Borrador'),
		('process', 'Procesado'),
		('cancel', 'Cancelado'),
	], string='Estado',default='draft',tracking=True)
	seller_id = fields.Many2one('hr.employee', string='Vendedor',tracking=True,required=True)
	seller_id_user = fields.Many2one('res.users', string='Vendedor',tracking=True,required=False)

	is_fiscal = fields.Boolean(string='Es Fiscal')

	checked = fields.Boolean(string='Verificado')


	def format_date_tz_maxcam(self,date):
		#format date to utz
		fmt = "%d-%m-%Y %H:%M:%S"
		tz = pytz.timezone("America/Caracas")
		nt = date.astimezone(tz)
		return nt.strftime(fmt)
	"""@api.depends("payment_approval_line.amount","payment_approval_line.amount_balance_use","payment_approval_line")
	def _calc_total_amount(self):
		_logger.info("DISPARO EL COMPUTE")
		_logger.info("self %s",self)
		for p in self:
			_logger.info("p.payment_approval_line %s",p.payment_approval_line)
			total = 0
			for line in p.payment_approval_line:
				_logger.info("line.amount %s",line.amount)
				_logger.info("line.amount_balance_use %s",line.amount_balance_use)
				total += line.amount + line.amount_balance_use
			p.amount_compute = total
			self._onchange_amount_compute()"""

	@api.onchange('amount_compute')
	def _onchange_amount_compute(self):
		_logger.info("SELF.AMOUNT COMPUTE %s",self.amount_compute)
		_logger.info("SELF.AMOUNT %s",self.amount)
		self.amount = self.amount_compute

	def cancel_payment(self):
		for l in self.payment_approval_line:
			if l.deposit_id and l.deposit_id.state != 'cancel':
				raise UserError("No puedes cancelar un recibo con lineas que tengan depositos asociados, por favor cancela el deposito primero")
			if l.payment_related:
				l.payment_related.action_draft()
				l.payment_related.action_cancel()
			#remover partials del saldo a favor
			domain = [
				("account_internal_type", "in", ("receivable", "payable")),
			]
			lines_invoice = l.invoice_id.line_ids.filtered_domain(domain)
			for linv in lines_invoice:
				partials = self.env['account.partial.reconcile'].sudo().search([('debit_move_id','=',linv.id)])
				partials.unlink()
			
		if self.is_fiscal:
			for line in self.payment_approval_line:
				ret = self.env['retention.register'].sudo().search([('invoice_id','=',line.invoice_id.id),('state','in',['draft','process'])])
				for r in ret:
					#cancelar asiento de retencion
					if r.move_id:
						r.move_id.button_draft()
						r.move_id.button_cancel()
					r.write({'state':'cancel'})
		for ml in self.payment_approval_methods:
			if ml.residual_payment and ml.residual_payment.state == 'posted':
				ml.residual_payment.action_draft()
				ml.residual_payment.action_cancel()

		self.state = 'cancel'


	def process_payment_batch(self):
		'''Compute the values for payments.
		:return: a list of payment values (dictionary).
		'''
		grouped = defaultdict(list)
		grouped_cash = defaultdict(list)
		tb = len(self.payment_approval_line.filtered_domain([('journal_id.type','=','bank')]))
		tc = len(self.payment_approval_line.filtered_domain([('journal_id.type','=','cash')]))
		_logger.info("cantidad de lineas con diario tipo banco %s",tb)
		_logger.info("cantidad de lineas con diario tipo cash %s",tc)
		#journal_id_maxcam
		#return False
		for obj in self.payment_approval_line.filtered_domain([('journal_id.type','=','bank'),('amount','>',0)]):
			grouped[obj.reference].append(obj)
		new_list = grouped.values()
		_logger.info("LISTA AGRUPADA POR NOMBRE DISTINTO A EFECTIVO %s",new_list)
		for obj_cash in self.payment_approval_line.filtered_domain([('journal_id.type','=','cash'),('amount','>',0)]):
			grouped_cash[obj_cash.journal_id.name].append(obj_cash)
		cash_list = grouped_cash.values()
		can_continue = True
		for balance_item in self.payment_approval_line.filtered_domain([('use_balance','=',True),('amount_balance_use','>',0)]):
			#js_assign_outstanding_line_maxcam
			
			if balance_item.invoice_id and balance_item.invoice_id.amount_residual > 0:
				total_balance = round(balance_item.amount_balance_use,2)
				available = self.env['account.move'].sudo()._compute_payments_partner_maxcam(balance_item.invoice_id.partner_id)
				_logger.info("available available available available %s",available)
				_logger.info("balance_item.amount_balance_use %s",total_balance)
				if round(available,2) >= total_balance:
					#no puede aplicarse porque el saldo a favor es menor a lo que toca aplicar
					lines_p = self.env['account.move'].sudo()._compute_payments_partner_maxcam_lines(balance_item.invoice_id.partner_id.id,round(balance_item.amount_balance_use,2))
					#lineas de APUNTE que deben cubrir ese monto
					#pass
					_logger.info("LINEAS DE PAGOS %s",lines_p)
					for l in lines_p:
						line_account = self.env['account.move.line'].sudo().browse(int(l))
						#linea de pago

						
						domain = [
							("account_internal_type", "in", ("receivable", "payable")),
							("reconciled", "=", False),
						]
						lines_invoice = balance_item.invoice_id.line_ids.filtered_domain(domain)
						#linea a pagar de facturas
						#amount_residual_currency
						_logger.info("este es el balance en total %s",total_balance)
						_logger.info("este es el monto de la linea DEL PAGO %s",abs(line_account.amount_residual_currency))

						for linv in lines_invoice:
							_logger.info("este es el monto adeudado en la factura %s",linv.amount_residual_currency)
							bal = line_account.amount_residual_currency if abs(line_account.amount_residual_currency) <= abs(linv.amount_residual_currency) else abs(linv.amount_residual_currency)
							_logger.info("balanace a mandar en el partial %s",bal)
							partials_vals_list = {
								'amount': abs(bal),
								'debit_amount_currency': abs(bal),
								'credit_amount_currency': abs(bal),
								'debit_move_id': linv.id,
								'credit_move_id': l,
							}
							total_balance-=abs(bal)
							_logger.info("PARTIALS EN SALDO A FAVOR %s",partials_vals_list)
							partials = self.env['account.partial.reconcile'].create(partials_vals_list)
						_logger.info("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL %s",l)
						#balance_item.write({"payment_related":l})
				else:
					_logger.info("el saldo a favor de la persona no cubre el monto de balance a usar %s",round(available,2))
					can_continue = False
					break
					#pass
		if not can_continue:
			return False,'Saldo a favor disponible no es suficiente'
		for g in new_list:
			payment_list = []
			inv_list = []
			total = 0
			for obj in g:
				if obj.invoice_id.amount_residual > 0:
					_logger.info("hacer pago de la factura %s",obj.invoice_id)
					_logger.info("sumar el monto %s",obj.amount)
					inv_list.append(obj.invoice_id.id)
					total+=obj.amount
					_logger.info("MEMO %s",obj.memo)
					line = {
						'invoice_id':obj.invoice_id.id,
						'partner_id':self.partner_id.id,
						'balance':obj.invoice_id.amount_residual,
						'amount':obj.amount,
						'payment_difference_handling':'open',
						#'writeoff_account_id':273,#duda en esto, el diario tiene una cofiguracion de cuenta de pago pendiente usar esa?
						'note':obj.reference,
						'foreign_payment_currency_rate':obj.foreign_payment_currency_rate,
						
					}
					
					payment_list.append((0,0,line))
			wizard = {
				'journal_id':g[0].journal_id.id,
				'payment_date':g[0].payment_date if g[0].payment_date else fields.date.context_today(self),#ojo debe ser context_today
				'cheque_amount':total,
				'is_customer':True,
				'total_amount':total,
				'invoice_payments':payment_list,
				'payment_method_id':1,#duda
				'company_id':self.env.user.company_id.id,
				'communication': str(g[0].memo),
			}
			#pasar por context inv_lis
			_logger.info("INV LIST %s",inv_list)
			apr = self.env['account.payment.register'].with_context({"maxcam_batch":True,"active_model":"account.move","active_ids":inv_list}).create(wizard)
			_logger.info("Este es el wizard creado %s",apr)
			payments = apr.make_payments()
			#self.env.cr.commit()
			_logger.info("Este es el pago retornado %s",payments)
			if len(payments)>0:
				for obj in g:
					obj.write({'payment_related':payments[0]})

			_logger.info("despues de disparar el make entry")
			#ojo con el return, cambiar status etc

		for g in cash_list:
			payment_list = []
			inv_list = []
			total = 0
			for obj in g:
				if obj.invoice_id.amount_residual > 0:
					_logger.info("hacer pago de la factura %s",obj.invoice_id)
					_logger.info("sumar el monto %s",obj.amount)
					inv_list.append(obj.invoice_id.id)
					total+=obj.amount
					line = {
						'invoice_id':obj.invoice_id.id,
						'partner_id':self.partner_id.id,
						'balance':obj.invoice_id.amount_residual,
						'amount':obj.amount,
						'payment_difference_handling':'open',
						#'writeoff_account_id':273,#duda en esto, el diario tiene una cofiguracion de cuenta de pago pendiente usar esa?
						'note':obj.reference,
						'foreign_payment_currency_rate':obj.foreign_payment_currency_rate,
					}
					payment_list.append((0,0,line))
			wizard = {
				'journal_id':g[0].journal_id.id,#este diario debe ser el diario del vendedor
				'payment_date':g[0].payment_date if g[0].payment_date else fields.date.context_today(self),#ojo debe ser context_today
				'cheque_amount':total,
				'is_customer':True,
				'total_amount':total,
				'invoice_payments':payment_list,
				'payment_method_id':1,#duda
				'company_id':self.env.user.company_id.id,
			}
			#pasar por context inv_lis
			_logger.info("INV LIST %s",inv_list)
			apr = self.env['account.payment.register'].with_context({"maxcam_batch":True,"active_model":"account.move","active_ids":inv_list}).create(wizard)
			_logger.info("Este es el wizard creado %s",apr)
			payments = apr.make_payments()
			_logger.info("Este es el pago retornado %s",payments)
			#self.env.cr.commit()
			if len(payments)>0:
				for obj in g:
					obj.write({'payment_related':payments[0]})

			_logger.info("despues de disparar el make entry")
			#ojo con el return, cambiar status etc
		

		
		for ml in self.payment_approval_methods:
			if ml.residual_payment and ml.residual_payment.state == 'draft':
				ml.residual_payment.action_post()
		
		self.write({'state':'process'})
		if self.is_fiscal:
			for line in self.payment_approval_line:
				ret = self.env['retention.register'].sudo().search([('invoice_id','=',line.invoice_id.id),('state','=','draft')])
				for r in ret:
					if r.move_id and r.invoice_id:
						if r.move_id.state == 'draft':
							r.move_id.action_post()
						#luego aplicarlo a la factura directo
						domain = [
							("account_internal_type", "in", ("receivable", "payable")),
							("reconciled", "=", False),
						]
						pay_term_lines = self.env['account.account'].sudo().search([('user_type_id.type','in',('receivable', 'payable'))]).ids
						domain_ret = [
							('account_id', 'in', pay_term_lines),
							('move_id.state', '=', 'posted'),
							#('partner_id', '=', int(partner_id)),
							
							('reconciled', '=', False),
							'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
						]
						_logger.info("move_ret.line_ids.filtered_domain(domain_ret) %s",r.move_id.line_ids.filtered_domain(domain_ret))
						all_lines = r.move_id.line_ids.filtered_domain(domain_ret) + r.invoice_id.line_ids.filtered_domain(domain)
						if all_lines:
							all_lines.reconcile()
					r.write({'state':'process'})

		try:
			template_id = self.env.ref('maxcam_payments.email_pago_procesado')
			if template_id:
				_logger.info("ENIVAR CORREO DE PAGO PROCESADO %s",self._origin.id)
				self.env['mail.template'].sudo().browse(template_id.id).send_mail(self._origin.id, force_send=True)			
		except Exception as e:
			_logger.info("error enviando correo de pago procesado %s",str(e))
			pass
		return True,'Procesado satisfactoriamente'
		#return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]

class PaymentApprovalLine(models.Model):
	_name = 'payment.approval.line'
	_description = 'Payment Approval Line'

	name = fields.Char(string="Nombre",required=False)
	payment_approval = fields.Many2one('payment.approval', string="Recibo asociado")
	invoice_id = fields.Many2one('account.move', string="Factura",
								 domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]",required=True)
	partner_id = fields.Many2one('res.partner', string='Cliente',related="invoice_id.partner_id")
	transfer_number = fields.Integer(string="Número de transferencia", help="Número de transferencia")

	amount = fields.Float(string="Monto", help="Monto",required=True)
	journal_id = fields.Many2one('account.journal', string="Diario", help="Diario",required=False) #no es obligatorio si usa saldo a favor
	amount_residual = fields.Monetary(string='Residual', related='invoice_id.amount_residual',
									  currency_field='currency_id')
	currency_id = fields.Many2one('res.currency')

	payment_related = fields.Many2one('account.payment', string='Pago Relacionado')

	foreign_payment_currency_id = fields.Many2one('res.currency', string="Moneda/Divisa",
												  default=lambda self: self.env.ref("base.VEF"))
	foreign_payment_currency_rate = fields.Float(string='Tasa', digits=(12, 2),
												 help='Guarda la tasa en que se calcula el total en la moneda foránea')

	cash_conciled = fields.Boolean(string='Efectivo Conciliado')


	#campos en caso de tener factura fiscal
	invoice_number = fields.Char(string='Número de la factura')
	total_invoice = fields.Float(string="Total Factura", help="Monto Total Factura")
	total_retention = fields.Float(string="Total Retenido", help="Monto Total Retenido")
	iva = fields.Float(string="IVA", help="IVA")
	subtotal = fields.Float(string="Base Imponible", help="Base Imponible")

	#campos en caso de que diario sea banco
	reference = fields.Char(string='Referencia',required=False) #obligatorio != efectivo
	holder = fields.Char(string='Titular')

	payment_date = fields.Date(string='Fecha del pago')#fields.Char(string='Fecha del pago')

	use_balance = fields.Boolean(string='Usar Saldo a favor')
	amount_balance_use = fields.Float(string='Saldo a favor a usar')

	memo = fields.Char(string='Memo')


	@api.model_create_multi
	def create(self, vals):
		#_logger.info("vals del crear linea %s",vals)
		for l in vals:
			_logger.info("Linea a crear %s",l)
			inv = self.env['account.move'].sudo().browse(l.get("invoice_id",False))
			journal = self.env['account.journal'].sudo().browse(l.get("journal_id",False))
			new_name = False
			if inv:
				new_name = str(inv.name) 
			if journal:
				new_name+=" - "+str(journal.name)
			if new_name:
				l.update({"name":new_name})
		lines_app = super(PaymentApprovalLine, self).create(vals)
		return lines_app

class PaymentApprovalmethods(models.Model):
	_name = 'payment.approval.methods'
	_description = 'Metodos de pago recibidos'
	_rec_name = 'journal_id'
	

	journal_id = fields.Many2one('account.journal', string='Metodo de pago',required=True)
	amount = fields.Float(string='Monto recibido',required=True)
	amount_compute = fields.Float(string='Monto calculado')
	currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string="Moneda",related='journal_id.currency_id')
	payment_approval = fields.Many2one('payment.approval', string="Recibo asociado")

	residual_payment = fields.Many2one('account.payment', string='Pago sobrante asociado')

	"""@api.depends("payment_approval.payment_approval_line")
	def _calc_total_amount(self):
		_logger.info("DISPARO EL COMPUTE DE METHODS")
		for p in self:
			total = 0
			methods = p.payment_approval.payment_approval_line.filtered_domain([('journal_id','=',p.journal_id.id)])
			for line in methods:
				total+= line.amount
			p.amount_compute = total"""

	"""@api.onchange('amount_compute')
	def _onchange_amount_compute(self):
		_logger.info("SELF.AMOUNT COMPUTE METHODS %s",self.amount_compute)
		_logger.info("SELF.AMOUNT METHODS %s",self.amount)
		self.amount = self.amount_compute"""
