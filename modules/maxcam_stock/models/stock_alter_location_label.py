import logging

from odoo import fields, models

_logger = logging.getLogger()


class StockAlterLocationLabel(models.Model):
    _name = 'stock.alter.location.label'
    _description = 'Etiqueta de la Ubicación Física'

    name = fields.Char('Nombre', required=True)