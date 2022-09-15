# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict

class RetentionRegisterMaxcam(models.Model):
	_name = 'retention.register'
	_description = 'Retenciones Notificadas'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	#_order = 'name'
	_rec_name = 'partner_id'
	_order = 'create_date desc'

	partner_id = fields.Many2one('res.partner', 'Cliente', help="Cliente",tracking=True)
	payment_approval = fields.Many2one('payment.approval', string="Recibo asociado")
	invoice_id = fields.Many2one('account.move', string="Factura",
								 domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]")
	journal_id = fields.Many2one('account.journal', string="Diario", help="Diario")
	invoice_number = fields.Char(string='Número de la factura')
	total_invoice = fields.Float(string="Total Factura", help="Monto Total Factura")
	total_retention = fields.Float(string="Total Retenido", help="Monto Total Retenido")
	iva = fields.Float(string="IVA", help="IVA")
	subtotal = fields.Float(string="Base Imponible", help="Base Imponible")
	state = fields.Selection([
		('draft', 'Borrador'),
		('process', 'Procesado'),
		('cancel', 'Cancelado'),
	], string='Estado',default='draft',tracking=True)
	seller_id = fields.Many2one('hr.employee', string='Vendedor',tracking=True)

	move_id = fields.Many2one('account.move', string='Asiento de retencion')

	image = fields.Binary(string='Documento')
	image_filename = fields.Char(string='Documento')
	note = fields.Char(string='Nota')

