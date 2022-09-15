import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class UpdatePriceLotMaxcamStock(models.TransientModel):
    _name = 'update_price_lot'
    _description = 'Actualización de precio en lote 1'

    lines = fields.One2many('update_price_lot_lines', 'update_price_parent', string='Lineas')

    update_type = fields.Selection([('fixed', 'Costo Fijo'), ('percent', 'Porcentaje'), ('manual', 'Manual')],
                                   string='Tipo de Actualización')
    percent = fields.Float(string='Porcentaje')
    fixed_cost = fields.Float(string='Costo')

    def process(self):
        _logger.info("procesar %s", self.lines)
        for l in self.lines:

            if self.update_type == 'manual':
                if l.product_id and l.new_cost > 0:
                    l.product_id.write({'standard_price': l.new_cost})
                else:
                    raise ValidationError("El costo debe ser mayor a 0")
            elif self.update_type == 'fixed':
                if self.fixed_cost > 0:
                    l.product_id.write({'standard_price': self.fixed_cost})
                else:
                    raise ValidationError("El costo debe ser mayor a 0")
            elif self.update_type == 'percent':
                if self.percent > 0:

                    p = self.percent + 1

                    new_cost = l.product_id.standard_price * p

                    l.product_id.write({'standard_price': new_cost})
                else:
                    raise ValidationError("El porcentaje debe ser mayor a 0")
            else:
                pass
        return True


class UpdatePriceLotLineMaxcamStock(models.TransientModel):
    _name = 'update_price_lot_lines'
    _description = 'Actualización de precio en lote 2'

    product_id = fields.Many2one('product.template', string='Producto')
    alternate_code = fields.Char(related='product_id.alternate_code')
    cost = fields.Float(string='Costo actual')
    new_cost = fields.Float(string='Nuevo Costo')
    update_price_parent = fields.Many2one('update_price_lot', string='Lote')

    update_type = fields.Selection(string='Tipo de Actualización', related='update_price_parent.update_type')

    @api.onchange('update_type')
    def _onchange_update_type(self):
        for l in self:
            if l.update_type in ['fixed', 'percent']:
                l.new_cost = 0
