# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveDispatchMaxcam(models.Model):
    _inherit = 'account.move'

    qty_packages = fields.Integer(string='Cantidad de bultos', compute="_compute_qty_packages")

    days_elapsed_collection = fields.Char(string='Dias transcurridos', compute="_compute_days_elapsed_collection",
                                          copy=False)

    @api.depends('reception_date_client', 'write_date')
    def _compute_days_elapsed_collection(self):
        for record in self:
            if record.move_type in ['out_invoice',
                                    'out_refund'] and record.reception_date_client and not record.currency_id.is_zero(
                    record.amount_residual):
                expired = fields.Date.from_string(fields.Date.context_today(self)) - record.reception_date_client
                expired = str(expired.days) + " Días"
            else:
                expired = ''
            record.days_elapsed_collection = expired

    @api.depends('picking_ids')
    def _compute_qty_packages(self):
        for record in self:
            if record.picking_ids:
                qty_packages = sum(record.picking_ids.mapped('qty_packages_dispatch_total') or 0)
            else:
                qty_packages = 0
            record.qty_packages = qty_packages

    @api.onchange('reception_date_client')
    def recompute_invoice_due_date(self):
        if self.move_type == 'out_invoice' and self.invoice_date_due and self.invoice_date and self.reception_date_client:
            if self.reception_date_client < self.invoice_date:
                raise UserError("Fecha de recepción del cliente no debe ser menor a la fecha de factura")

            diff = self.invoice_date_due - self.invoice_date
            self.invoice_date_due = self.reception_date_client + timedelta(days=diff.days)

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        for record in self:
            if not record.reception_date_client and record.move_type in ['out_invoice', 'out_refund']:
                raise ValidationError(_('Assign a receipt date to post payments'))
        return super(AccountMoveDispatchMaxcam, self).action_register_payment()

    def js_assign_outstanding_line(self, line_id):
        ''' Called by the 'payment' widget to reconcile a suggested journal item to the present
        invoice.

        :param line_id: The id of the line to reconcile with the current invoice.
        '''
        for record in self:
            if not record.reception_date_client and record.move_type in ['out_invoice', 'out_refund']:
                raise ValidationError(_('Assign a receipt date to post payments'))
        return super(AccountMoveDispatchMaxcam, self).js_assign_outstanding_line(line_id)
