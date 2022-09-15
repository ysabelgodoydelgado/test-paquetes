# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class MaxcamProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(MaxcamProductProduct, self)._name_search(name=name, args=args, operator=operator, limit=limit,
                                                             name_get_uid=name_get_uid)
        if len(name) != 0:
            operator = '='
            args = expression.AND([args, [('alternate_code', operator, name)]])
            ids = self.search(args, limit=limit).ids
            res = res + ids
        return res

    # @api.onchange('list_price')
    # def _onchange_list_price(self):
    #     print("222222222222")
    #     if self.list_price and self.list_price <= 0:
    #         raise UserError(_('El precio de venta no puede ser cero (0) o negativo'))
    #
    # @api.onchange('standard_price')
    # def _onchange_standard_price(self):
    #     print("standard_price", self.standard_price)
    #     if self.standard_price and self.standard_price <= 0:
    #         raise UserError(_('El costo no puede ser cero (0)'))
    #     if self.standard_price >= self.list_price:
    #         raise UserError(_('El Precio de venta no puede ser mayor o igual al costo'))
