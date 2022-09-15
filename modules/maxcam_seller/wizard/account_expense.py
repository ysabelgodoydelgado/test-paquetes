# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountExpenseWizard(models.TransientModel):
    _name = 'account.expense.wizard'
    _description = 'create one or more expense records from invoices with the associated vendor.'

    move_ids = fields.Many2many('account.move', string='Seller invoices')
    type_expense = fields.Selection([('per_invoice', 'generate an expense per invoice'),
                                     ('all_invoices', 'generate an expense with all invoices')], required=True,
                                    default='per_invoice')

    @api.model
    def default_get(self, fields_list):
        values = super(AccountExpenseWizard, self).default_get(fields_list)
        active_move_ids = self.env['account.move']
        if self.env.context['active_model'] == 'account.move' and 'active_ids' in self.env.context:
            active_move_ids = self.env['account.move'].browse(self.env.context['active_ids'])
        if len(active_move_ids.seller_id) > 1:
            raise UserError(_('You can only create expenses for the same seller'))
        if len(active_move_ids.currency_id) > 1:
            raise UserError(_('You can only create expenses with the same currency'))
        if len(active_move_ids.seller_id) > 1:
            raise UserError(_('All customers must have a vendor'))
        values['move_ids'] = [(6, 0, active_move_ids.ids)]
        return values

    def generate_expense(self):
        self.ensure_one()
        if self.type_expense == 'per_invoice':
            self.per_invoice()
        else:
            self.all_invoices()

    def per_invoice(self):
        expense_json = []
        for move in self.move_ids:
            invoice_id = []
            invoice_id.append(move.id)
            expense_line = self.expense_json(invoice_id, move.seller_id, move.name, move.total_commission,
                                             move.currency_id.id)
            expense_json.append(expense_line)
        if len(expense_json) > 0:
            self.expense(expense_json)
            self.move_ids.write({'paid_seller': 'process'})

    def all_invoices(self):
        reference = ""
        total_commission = 0
        seller = 0
        currency = 0
        invoice_ids = []
        for move in self.move_ids:
            reference += move.name + ' - '
            total_commission += move.total_commission
            seller = move.seller_id
            currency = move.currency_id.id
            invoice_ids.append(move.id)
        if len(self.move_ids) > 0:
            expense_line = self.expense_json(invoice_ids, seller, reference, total_commission, currency)
            self.expense(expense_line)
            self.move_ids.write({'paid_seller': 'process'})

    def expense_json(self, invoice_ids, seller=None, reference='', amount=0, currency=False):
        product = self.env.ref('maxcam_seller.product_product_sellers_payment').id

        expense_line_values = {
            'name': _("Comisión: %s", seller.name),
            'product_id': product,
            'unit_amount': amount,
            'quantity': 1.0,
            'date': fields.date.today(),
            'tax_ids': [(5, 0, 0)],
            'reference': reference,
            'employee_id': seller.id,
            'company_id': self.env.user.company_id.id,
            'account_id': False,
            'currency_id': currency,
            'paid_seller': True,
            'invoice_ids': [(6, 0, invoice_ids)],
        }
        return expense_line_values

    def expense(self, expense_json):
        try:
            self.env['hr.expense'].create(expense_json)
        except Exception as e:
            _logger.error("Error al Registrar gasto %s", e)
