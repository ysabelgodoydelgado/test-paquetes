from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = "stock.location"

    stock_alter_location_id = fields.Many2one("stock.picking.alter.location")
