# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round
class MaxcamProductTemplate(models.Model):
    _inherit = 'product.template'

    _sql_constraints = [
        (
            'default_code_unique', 'unique(default_code)',
            "¡La referencia interna debe ser única! Por favor, elija otro."),
        ('alternate_code_unique', 'unique(alternate_code)', "¡El código alterno debe ser único! Por favor, elija otro.")
    ]

    @api.model
    def _get_domain(self):
        external_location = self.env.ref("stock.stock_location_output")
        _logger.warning(f"Stock Id > {external_location}")

        return [('id', "!=", external_location.id), ('usage', '=', 'internal')]

    alternate_code = fields.Char('Alternate Code', copy=False, help="alternative identification code")

    brand_id = fields.Many2one('product.brand', string="Brand to product", help="Trademarks related to the product")
    sales_policy = fields.Integer(default=0)

    quantity_package = fields.Integer(string="Quantity per Package", default=0)

    available_qty = fields.Float(
        'Amount in real hand', compute='_get_warehouse_quantity', compute_sudo=False, digits='Product Unit of Measure',
    )  # _compute_available_qty store=True

    available_qty_store = fields.Float(
        'Cantidad disponible en almacen de ventas', compute='_get_warehouse_quantity_store', compute_sudo=False,
        digits='Product Unit of Measure',
        store=True)  # _compute_available_qty store=True
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=False, group_expand='_read_group_categ_id',
        required=True, help="Select category for the current product")

    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', required=True,
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')],
                                default=lambda self: self.env.company.account_sale_tax_id)

    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist', store=True,
        help='Technical field. Used for searching on pricelists, not stored in database.')

    list_price = fields.Float('Sales Price', default=1.0, digits='Product Price', compute='_compute_list_price',
                              help="Price at which the product is sold to customers.")

    warehouse_quantity = fields.Char(compute='_get_warehouse_quantity', string='Sin Reserva en almacén de VENTAS')

    warehouse_quantity_all = fields.Char(compute='_get_warehouse_quantity_all', string='Sin Reserva por almacén')
    pick_location = fields.Many2one("stock.location",
                                    string="Ubicación física",
                                    domain=_get_domain)

    def write(self, vals):
        res = super().write(vals)
        self._handle_pick_location()

        return res

    def _handle_pick_location(self):
        _logger.warning("_handle_pick_location %s", self.product_variant_id)
        ref_stock_alter_location = self.env["stock.picking.alter.location"].search(
            [('product_id', '=', self.product_variant_id.id)])

        if self.pick_location and not ref_stock_alter_location:
            pick_quant = self.env['stock.quant'].search(
                [('product_tmpl_id', '=', self.id), ('location_id', '=', self.pick_location.id)], limit=1)

            picking_alter_location = self.env["stock.picking.alter.location"].create({
                'product_id': self.product_variant_id.id,
                'pick_location': self.pick_location.id,
                'pick_quantity': pick_quant.quantity
            })
            picking_alter_location.write({
                'stock_alter_location_lines': self._get_quants_for_alter_lines(picking_alter_location.id)
            })

            return picking_alter_location

        return False

    def _get_quants_for_alter_lines(self, stock_alter_location_id):
        alter_lines_list = []
        external_location = self.env.ref("stock.stock_location_output")

        quants = self.env['stock.quant'].search(
            [('product_tmpl_id', '=', self.id), ('location_id', '!=', self.pick_location.id), ('on_hand', '=', True)])
        for quant in quants:
            if quant.location_id.id != external_location.id:
                alter_lines_list.append((0, 0, {
                    'location_id': quant.location_id.id,
                    'stock_alter_location_id': stock_alter_location_id,
                    'available_qty': quant.quantity
                }))

        return alter_lines_list

    @api.depends('pricelist_id', 'categ_id', 'standard_price')
    def _compute_list_price(self):
        for record in self:
            list_price = 0
            if record.pricelist_id and record.categ_id.id:
                item_pricelist = record.env['product.pricelist.item'].search([('categ_id', '=', record.categ_id.id),
                                                                              ('pricelist_id', '=',
                                                                               record.pricelist_id.id)], limit=1)
                if item_pricelist and item_pricelist.compute_price == 'formula':
                    percentage = item_pricelist.price_discount * -1
                    percentage = percentage / 100
                    list_price = record.standard_price + (record.standard_price * percentage)
            else:
                list_price = record.standard_price + 1
            record.list_price = list_price

    def get_filtered_record_percentage(self):
        # active_ids = self.env.context.get('active_ids', [])
        return self.my_action_percentage()

    @api.model
    def my_action_percentage(self):
        try:
            form_view_id = self.env.ref("maxcam_stock.view_update_price_percentage_venfood_form_5").id
        except Exception as e:
            form_view_id = False
        lines = []
        for l in self.ids:
            product = self.env['product.template'].browse(l)
            obj = {'product_id': product.id,
                   'new_cost': 0,
                   'cost': product.standard_price,
                   }
            _logger.info("objeto a la linea %s", obj)
            lines.append(obj)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Actualizar Costos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update_price_lot',
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            # 'target': 'inline',
            'target': 'new',
            'flags': {'form': {'action_buttons': False}},
            'context': {
                'default_lines': lines,
                'default_update_type': 'manual',
            },
        }

    def button_dummy(self):
        # TDE FIXME: this button is very interesting
        return True

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if float_is_zero(self.list_price, precision_digits=2):
            raise UserError(_('El precio de venta no puede ser cero (0) o negativo'))

    @api.constrains('standard_price')
    def _constrains_standar_price(self):
        for record in self:
            if float_is_zero(record.standard_price, precision_digits=2):
                # pass
                raise UserError(_('El costo no puede ser cero (0)'))
            elif record.standard_price >= record.list_price:
                raise UserError(_('El Costo no puede ser mayor o igual al precio de venta'))

    @api.constrains('list_price')
    def _constrains_list_price(self):
        for record in self:

            if record.type == 'product' and float_is_zero(record.list_price, precision_digits=2):
                # pass
                raise UserError(_('El Precio no puede ser cero (0)'))

    @api.depends('qty_available', 'outgoing_qty')
    def _get_warehouse_quantity_store(self):
        for record in self:
            available_qty = 0
            warehouse_quantity_text = ''
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
            if product_id:
                quant_ids = self.env['stock.quant'].sudo().search(
                    [('product_id', '=', product_id[0].id), ('location_id.usage', '=', 'internal')])
                t_warehouses = {}
                rounding = product_id.uom_id.rounding
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id: 0})
                        t_warehouses[quant.location_id] += float_round(quant.quantity - quant.reserved_quantity,
                                                                       precision_rounding=rounding)

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search(
                            [('lot_stock_id', '=', location1.id), ('is_sale_storage', '=', True)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.code not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.code: 0})
                        tt_warehouses[warehouse_id.code] += t_warehouses[location]

                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                        warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(
                            tt_warehouses[item])
                        available_qty = tt_warehouses[item]
            record.available_qty_store = available_qty

    def _get_warehouse_quantity(self):
        for record in self:
            available_qty = 0
            warehouse_quantity_text = ''
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
            if product_id:
                quant_ids = self.env['stock.quant'].sudo().search(
                    [('product_id', '=', product_id[0].id), ('location_id.usage', '=', 'internal')])
                t_warehouses = {}
                rounding = product_id.uom_id.rounding
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id: 0})
                        t_warehouses[quant.location_id] += float_round(quant.quantity - quant.reserved_quantity,
                                                                       precision_rounding=rounding)

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search(
                            [('lot_stock_id', '=', location1.id), ('is_sale_storage', '=', True)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.code not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.code: 0})
                        tt_warehouses[warehouse_id.code] += t_warehouses[location]

                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                        warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(
                            tt_warehouses[item])
                        available_qty = tt_warehouses[item]
            record.warehouse_quantity = warehouse_quantity_text
            record.available_qty = available_qty
            # _logger.info(tt_warehouses)

    def _get_warehouse_quantity_all(self):
        for record in self:
            warehouse_quantity_text = ''
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
            if product_id:
                quant_ids = self.env['stock.quant'].sudo().search(
                    [('product_id', '=', product_id[0].id), ('location_id.usage', '=', 'internal')])
                t_warehouses = {}
                rounding = product_id.uom_id.rounding
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id: 0})
                        t_warehouses[quant.location_id] += float_round(quant.quantity - quant.reserved_quantity,
                                                                       precision_rounding=rounding)

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id', '=', location1.id)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.code not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.code: 0})
                        tt_warehouses[warehouse_id.code] += t_warehouses[location]

                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                        warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(
                            tt_warehouses[item])
            record.warehouse_quantity_all = warehouse_quantity_text
            # _logger.info(tt_warehouses)
