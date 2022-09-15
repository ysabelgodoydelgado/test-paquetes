import logging

from odoo import _, api
from odoo.exceptions import ValidationError
from odoo.fields import (
    Char,
    Float,
    One2many,
    Many2one
)
from odoo.models import Model

_logger = logging.getLogger()


class StockPickingAlterLocation(Model):
    _name = "stock.picking.alter.location"
    _description = "Ubicaciones alternas a las de Odoo"

    pick_quantity = Float("Cantidades Físicas")
    total_quantity = Float("Cantidad en otras ubicaciones", compute="_total_quantity_in_locations")
    min_quantity = Float("Cantidad Minima")
    max_quantity = Float("Cantidad Máxima")

    name = Char("Nombre del Producto", related="product_id.name")
    label_id = Many2one("stock.alter.location.label", string="Etiqueta")
    product_id = Many2one("product.product", string="Producto")
    pick_location = Many2one("stock.location", string="Ubicación Física", related="product_id.pick_location")
    stock_alter_location_lines = One2many("stock.picking.alter.location.line",
                                          "stock_alter_location_id",
                                          string="Otras ubicaciones del producto")

    @api.constrains("pick_quantity")
    def _check_quantity_boundaries(self):
        for alter_location in self:
            if alter_location.pick_quantity < alter_location.min_quantity:
                raise ValidationError(_(f"La cantidad físicas no puede ser menor a {alter_location.min_quantity}"))
            if alter_location.pick_quantity > alter_location.max_quantity and alter_location.max_quantity > 0:
                raise ValidationError(_(f"La cantidad físicas no puede ser mayor a {alter_location.max_quantity}"))

    def action_change_product_quantities(self):
        view = self.env.ref("maxcam_stock.move_alter_location_qtities_wizard_view_form")
        list_of_locations = [location_line.location_id.id for location_line in self.stock_alter_location_lines]
        list_of_locations.append(self.pick_location.id)

        return {
            'name': _("Cambiar cantidades entre ubicaciones"),
            'type': "ir.actions.act_window",
            'view_mode': "form",
            'res_model': "move.alter.location.qtities.wizard",
            'views': [(view.id, "form")],
            'view_id': view.id,
            'target': 'new',
            'context': dict(default_to_location=self.pick_location.id,
                            default_stock_alter_location_id=self.id,
                            pick_boundaries={'min': self.min_quantity, 'max': self.max_quantity},
                            domain_locations=list_of_locations)
        }

    def _total_quantity_in_locations(self):
        for alter_location in self:
            total_quantity = float(sum([alter_location_line.available_qty for alter_location_line in
                                        alter_location.stock_alter_location_lines]))
            alter_location.total_quantity = total_quantity
