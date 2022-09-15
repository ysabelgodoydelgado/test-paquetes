# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaxcamFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    internal = fields.Boolean(string="Internal", default=False)
