# -*- coding: utf-8 -*-
import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderStockMaxCam(models.Model):
    _inherit = "sale.order"

    @api.constrains("order_line")
    def _constrains_order_line_sales_policiy(self):
        for record in self:
            if len(record.order_line) > 0:
                for line in record.order_line:
                    if (
                        line.product_id.sales_policy > 1
                        and line.product_id.available_qty >= line.product_id.sales_policy
                        and line.product_uom_qty % line.product_id.sales_policy != 0
                    ):
                        raise ValidationError(
                            _(
                                "The product %s has a Sales Policy, the quantity to be sold must"
                                "be a multiple of the same or %s"
                                % (line.product_id.name, line.product_id.sales_policy)
                            )
                        )

    @api.constrains("order_line")
    def _check_qty_available(self):
        overdraw_inventory = self.env["ir.config_parameter"].sudo().get_param("overdraw_inventory")
        if overdraw_inventory:
            for record in self:
                record.ensure_one()
                for line in record.order_line:
                    if line.product_id.type == "product":
                        if line.product_uom_qty > line.product_id.free_qty:
                            # "The quantity of the product %s exceeds what is available (%i)"
                            raise ValidationError(
                                _("La cantidad de producto %s excede lo disponible (%i)")
                                % (line.product_id.name, line.product_id.free_qty)
                            )

    def action_confirm(self):
        res = super().action_confirm()

        for sale_order in self:
            sale_order.generate_commission_image_for_sale_order()

        return res

    @api.model
    def generate_commission_image_for_sale_order(self):
        CommissionPolicy = self.env["commission.policy"]
        commissions = {
            "client": CommissionPolicy.get_commission("client"),
            "product": {
                "product": CommissionPolicy.get_commission("product", "product"),
                "category": CommissionPolicy.get_commission("product", "category"),
                "brand": CommissionPolicy.get_commission("product", "brand"),
            },
            "all": CommissionPolicy.get_commission("all"),
        }

        for sale_order in self:
            outs = sale_order.picking_ids.filtered(lambda x: x.picking_type_id.code == "outgoing")
            for line in sale_order.order_line:
                cancel_line_comparation = False
                if (
                    line.product_id.id in commissions["product"]["product"].products_id.ids
                    and not cancel_line_comparation
                ):
                    commission = commissions["product"]["product"].filtered(
                        lambda c: line.product_id.id in c.products_id.ids
                    )
                    commission.get_or_create_commission_image(outs, "product", "product")
                    cancel_line_comparation = True
                if (
                    line.product_id.categ_id.id
                    in commissions["product"]["category"].categories_id.ids
                    and not cancel_line_comparation
                ):
                    commission = commissions["product"]["category"].filtered(
                        lambda c: line.product_id.categ_id.id in c.products_id.categories_id.ids
                    )
                    commission.get_or_create_commission_image(outs, "product", "category")
                    cancel_line_comparation = True
                if (
                    line.product_id.brand_id.id in commissions["product"]["brand"].brands_id.ids
                    and not cancel_line_comparation
                ):
                    commission = commissions["product"]["brand"].filtered(
                        lambda c: line.product_id.brand_id.id in c.brands_id.ids
                    )
                    _logger.warning(commission)
                    commission.get_or_create_commission_image(outs, "product", "brand")
                    cancel_line_comparation = True
                if (
                    sale_order.partner_id.id in commissions["client"].clients_id.ids
                    and not cancel_line_comparation
                ):
                    commission = commissions["client"].filtered(
                        lambda c: sale_order.partner_id.id in c.clients_id.ids
                    )
                    commission.get_or_create_commission_image(outs, "client")
                    cancel_line_comparation = True
                if not cancel_line_comparation:
                    commissions["all"].get_or_create_commission_image(outs, "all")
