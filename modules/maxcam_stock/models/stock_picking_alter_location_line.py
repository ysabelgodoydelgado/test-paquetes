import logging

from odoo import _, api
from odoo.exceptions import UserError, ValidationError
from odoo.fields import (
    Float,
    Many2one
)
from odoo.models import Model

_logger = logging.getLogger()


class StockPickingAlterLocationLine(Model):
    _name = "stock.picking.alter.location.line"
    _description = "Linea de la Ubicación Alterna"

    location_id = Many2one("stock.location", string="Ubicación del Producto")
    stock_alter_location_id = Many2one("stock.picking.alter.location")
    available_qty = Float("Cantidades Disponibles")