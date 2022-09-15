# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class Client(models.Model):
    _inherit = 'res.country.state'

    state = fields.Selection([
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ], 'Estatus', required=True, default='active')
