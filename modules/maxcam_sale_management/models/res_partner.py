# -*- coding: utf-8 -*-
import logging


from odoo.exceptions import UserError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResPartnerMaxCam(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ('default_vat_unique', 'unique(vat)', "¡El RIF debe ser único! Por favor, elija otro."),
        ]

    # credit_limit = fields.Float(string='Credit Limit', default=-1)
    customer = fields.Boolean(string="client", default=False)
    supplier = fields.Boolean(string="supplier", default=False)

    @api.onchange('customer')
    def _onchange_customer(self):
        if self.customer:
            self._increase_rank('customer_rank')
        else:
            self._increase_rank('customer_rank', (self.customer_rank * -1))

    @api.onchange('supplier')
    def _onchange_supplier(self):
        if self.supplier:
            self._increase_rank('supplier_rank')
        else:
            self._increase_rank('supplier_rank', (self.supplier_rank * -1))

    @api.model
    def _commercial_fields(self):
        """ Returns the list of fields that are managed by the commercial entity
        to which a partner belongs. These fields are meant to be hidden on
        partners that aren't `commercial entities` themselves, and will be
        delegated to the parent `commercial entity`. The list is meant to be
        extended by inheriting classes. """
        res = super(ResPartnerMaxCam, self)._commercial_fields()
        res.remove('vat')
        return res

    # @api.constrains('credit_limit')
    # def _constraints_credit_limit(self):
    #     for record in self:
    #         print("record.credit_limit-->", record.credit_limit)
    #         if record.credit_limit < 0:
    #             raise UserError(_('El limite de credito del cliente no puede ser negativo'))

    # @api.onchange('credit_limit')
    # def _onchange_credit_limit(self):
    #     if self.credit_limit < 0:
    #         raise UserError(_('El limite de credito del cliente no puede ser negativo'))

    def _cron_execute_delivery_free(self):
        try:
            partner = self.env['res.partner'].search([])
            partner.write({'property_delivery_carrier_id': 8})
        except UserError as e:
            _logger.exception(e)
