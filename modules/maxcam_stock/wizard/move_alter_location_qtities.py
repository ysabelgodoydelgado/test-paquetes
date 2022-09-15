import logging

from odoo import _, api
from odoo.exceptions import UserError
from odoo.fields import (
    Float,
    Many2one,
)
from odoo.models import TransientModel

_logger = logging.getLogger()


class MoveAlterLocationQtitiesWizard(TransientModel):
    _name = "move.alter.location.qtities.wizard"
    _description = "Wizard para mover las cantidades físicas a las otras ubicaciones del producto."

    @api.model
    def _get_domain(self):
        external_location = self.env.ref("stock.stock_location_output")
        domain_locations = self.env.context.get("domain_locations")

        return [('id', "!=", external_location.id), ('usage', '=', 'internal'), ('id', 'in', domain_locations)]

    @api.model
    def _get_to_domain(self):
        external_location = self.env.ref("stock.stock_location_output")

        return [('id', "!=", external_location.id), ('usage', '=', 'internal')]

    transfer_quantity = Float("Cantidades a Transferir")

    from_location = Many2one("stock.location", string="Desde", domain=_get_domain)
    to_location = Many2one("stock.location", string="Hasta", domain=_get_to_domain)
    stock_alter_location_id = Many2one("stock.picking.alter.location")

    def action_transfer_quantities(self):
        pick_boundaries = self.env.context.get('pick_boundaries')

        if self.from_location.id == self.stock_alter_location_id.pick_location.id:
            stock_alter_location_line = self.stock_alter_location_id.stock_alter_location_lines.filtered(
                lambda line: line.location_id.id == self.to_location.id)

            if self.transfer_quantity >= self.stock_alter_location_id.pick_quantity:
                raise UserError(_("No puedes transferir más que la cantidad disponible en la ubicación física."))
            if (self.stock_alter_location_id.pick_quantity - self.transfer_quantity) <= pick_boundaries['min']:
                raise UserError(_(f"Las cantidades físicas no puede quedar por debajo de {pick_boundaries['min']}"))

            self.stock_alter_location_id.pick_quantity -= self.transfer_quantity

            if stock_alter_location_line:
                stock_alter_location_line.available_qty += self.transfer_quantity
            else:
                self.stock_alter_location_id.write({
                    'stock_alter_location_lines': [(0, 0, {
                        'location_id': self.to_location.id,
                        'available_qty': self.transfer_quantity
                    })]
                })
        elif self.to_location.id == self.stock_alter_location_id.pick_location.id:
            stock_alter_location_line = self.stock_alter_location_id.stock_alter_location_lines.filtered(
                lambda line: line.location_id.id == self.from_location.id)

            if not self.stock_alter_location_id.stock_alter_location_lines:
                raise UserError(_("No existen ubicaciones para transferir a la ubicación física."))
            if not stock_alter_location_line.available_qty:
                raise UserError(_("No hay cantidades disponibles en la ubicación para transferir"))
            if self.transfer_quantity > stock_alter_location_line.available_qty:
                raise UserError(
                    _(f"Las cantidades en {stock_alter_location_line.location_id.display_name} no pueden sobrepasar las disponibles."))
            if (self.transfer_quantity + self.stock_alter_location_id.pick_quantity) > pick_boundaries["max"]:
                raise UserError(_("La cantidad a transferir supera la cantidad máxima de la ubicación física."))

            self.stock_alter_location_id.pick_quantity += self.transfer_quantity
            stock_alter_location_line.available_qty -= self.transfer_quantity
        else:
            from_alter_location_line = self.stock_alter_location_id.stock_alter_location_lines.filtered(
                lambda line: line.location_id.id == self.from_location.id)
            to_alter_location_line = self.stock_alter_location_id.stock_alter_location_lines.filtered(
                lambda line: line.location_id.id == self.to_location.id)

            if from_alter_location_line.available_qty - self.transfer_quantity < 0:
                raise UserError(_("No puedes transferir más que la cantidad disponible en la ubicación."))

            from_alter_location_line.available_qty -= self.transfer_quantity
            if to_alter_location_line:
                to_alter_location_line.available_qty += self.transfer_quantity
            else:
                self.stock_alter_location_id.write({
                    'stock_alter_location_lines': [(0, 0, {
                        'location_id': self.to_location.id,
                        'available_qty': self.transfer_quantity
                    })]
                })
