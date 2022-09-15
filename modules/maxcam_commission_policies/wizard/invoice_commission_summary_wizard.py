import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class InvoiceCommissionSummaryWizard(models.TransientModel):
    _name = 'invoice.commission.summary.wizard'
    _description = 'Invoice Commission Summary Wizard'

    name = fields.Char(string="Name", required=True)
    invoice_line_ids = fields.Many2many('account.move.line', 'commission_sumary_rel', string="Invoice Lines")
