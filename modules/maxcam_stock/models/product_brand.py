# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Brand(models.Model):
    _name = 'product.brand'
    _description = 'Brands'

    _sql_constraints = [
        ('name_unique', 'unique(name)', "The Name must be unique! Please choose another.")]

    active = fields.Boolean("Active", default=True)
    name = fields.Char(string="Name", required=True, help="Brand name")
    partner_id = fields.Many2one('res.partner', string='Provider', help="Select the brand supplier")

    @api.onchange('name')
    def _onchange_capitalize_name(self):
        if self.name:
            self.name = self.name.capitalize()
            self.name = " ".join(self.name.split())
