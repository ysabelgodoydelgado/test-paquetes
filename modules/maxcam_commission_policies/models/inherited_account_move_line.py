import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    commission = fields.Float(string="Comisión", compute="_compute_commission")

    @api.depends(
        "move_id.picking_ids", "move_id.picking_ids.commission_images_id", "move_id.collection_days"
    )
    def _compute_commission(self):
        for line in self:
            product = line.product_id
            move = line.move_id
            partner = move.partner_id

            picking = move.picking_ids.filtered(lambda p: p.picking_type_id.code == "outgoing")
            commissions = {
                "client": picking.commission_images_id.filtered(
                    lambda c: c.policy_type == "client"
                ),
                "product": {
                    "product": picking.commission_images_id.filtered(
                        lambda c: c.policy_type == "product"
                        and c.product_commission_type == "product"
                    ),
                    "category": picking.commission_images_id.filtered(
                        lambda c: c.policy_type == "product"
                        and c.product_commission_type == "category"
                    ),
                    "brand": picking.commission_images_id.filtered(
                        lambda c: c.policy_type == "product"
                        and c.product_commission_type == "brand"
                    ),
                },
                "all": picking.commission_images_id.filtered(lambda c: c.policy_type == "all"),
            }

            if (
                move.move_type == "out_invoice"
                and move.last_payment_date
                and product.type == "product"
            ):
                if product.id in commissions["product"]["product"].products_id.ids:
                    commission = commissions["product"]["product"].filtered(
                        lambda c: product.id in c.products_id.ids
                    )
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                elif product.categ_id.id in commissions["product"]["category"].categories_id.ids:
                    commission = commissions["product"]["category"].filtered(
                        lambda c: product.categ_id.id in c.categories_id.ids
                    )
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                elif product.brand_id.id in commissions["product"]["brand"].brands_id.ids:
                    commission = commissions["product"]["brand"].filtered(
                        lambda c: product.brand_id.id in c.brands_id.ids
                    )
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                elif partner.id in commissions["client"].clients_id.ids:
                    commission = commissions["client"].filtered(
                        lambda c: partner.id in c.clients_id.ids
                    )
                    line.commission = commission.commission_line_ids.filtered(
                        lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                        or (cl.date_from <= move.collection_days and cl.date_until == 0)
                    ).commission
                else:
                    line.commission = (
                        commissions["all"]
                        .commission_line_ids.filtered(
                            lambda cl: cl.date_from <= move.collection_days <= cl.date_until
                            or (cl.date_from <= move.collection_days and cl.date_until == 0)
                        )
                        .commission
                    )
            else:
                line.commission = 0.0
