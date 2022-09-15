# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerSeller(models.Model):
    _inherit = 'res.partner'

    seller_id = fields.Many2one('hr.employee', string='Seller', tracking=1)

    @api.model
    def _commercial_fields(self):
        """ Returns the list of fields that are managed by the commercial entity
        to which a partner belongs. These fields are meant to be hidden on
        partners that aren't `commercial entities` themselves, and will be
        delegated to the parent `commercial entity`. The list is meant to be
        extended by inheriting classes. """
        res = super(ResPartnerSeller, self)._commercial_fields()
        res.append('seller_id')
        return res
