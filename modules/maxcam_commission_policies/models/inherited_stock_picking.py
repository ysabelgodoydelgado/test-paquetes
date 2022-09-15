import logging
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    commission_images_id = fields.Many2many(
        "commission.policy.image",
        "commission_policy_image_picking_rel",
        string="Historico de Comisiones",
    )

    def cron_action_assign_general_commission_to_picking(self):
        general_commission = self.env["commission.policy"].get_commission("all")
        uninvoiced_pickings_without_commission = self.search(
            [
                ("state", "not in", ["cancel", "draft"]),
                ("invoice_id", "=", False),
                ("picking_type_id", "=", 2),
                ("commission_images_id", "=", False),
            ]
        )
        invoiced_pickings_without_commission = self.search(
            [
                ("state", "not in", ["cancel", "draft"]),
                ("invoice_id", "!=", False),
                ("invoice_id.paid_seller", "=", "not_paid"),
                ("picking_type_id", "=", 2),
                ("commission_images_id", "=", False),
            ]
        )

        for picking in uninvoiced_pickings_without_commission:
            _logger.warning("==========PICKING: %s", picking)
            _logger.warning("just checkin' uninvoiced")
            general_commission.get_or_create_commission_image(picking, "all")

        for picking in invoiced_pickings_without_commission:
            _logger.warning("==========PICKING: %s", picking)
            _logger.warning("just checkin' invoiced")
            general_commission.get_or_create_commission_image(picking, "all")

    def cron_set_false_picking_images(self):
        uninvoiced_pickings_without_commission = self.search(
            [
                ("state", "not in", ["cancel", "draft"]),
                ("invoice_id", "=", False),
                ("picking_type_id", "=", 2),
            ]
        )
        invoiced_pickings_without_commission = self.search(
            [
                ("state", "not in", ["cancel", "draft"]),
                ("invoice_id", "!=", False),
                ("invoice_id.paid_seller", "=", "not_paid"),
                ("picking_type_id", "=", 2),
            ]
        )

        for picking in uninvoiced_pickings_without_commission:
            _logger.warning("==========PICKING: %s", picking)
            _logger.warning("just checkin' uninvoiced")
            picking.commission_images_id = False

        for picking in invoiced_pickings_without_commission:
            _logger.warning("==========PICKING: %s", picking)
            _logger.warning("just checkin' invoiced")
            picking.commission_images_id = False

    def exclude_out_from_older_general_commissons(self):
        images = self.env["commission.policy.image"].get_image_commission("all")
        active_image = images[0]
        unactive_images = images[1:]
        for image in unactive_images:
            active_image.pickings_id -= image.pickings_id

    def reset_product_brand_commission(self):
        CommissionPolicy = self.env["commission.policy"]

        sale_orders = self.env["sale.order"].search(
            [
                ("create_date", ">=", datetime(2022, 8, 4)),
                ("create_date", "<=", datetime.now()),
            ]
        )
        outs = sale_orders.picking_ids
        outs = outs.filtered(lambda x: x.picking_type_code == "outgoing")
        commissions = {
            "client": CommissionPolicy.get_commission("client"),
            "product": {
                "brand": CommissionPolicy.get_commission("product", "brand"),
            },
            "all": CommissionPolicy.get_commission("all"),
        }

        for out in outs:
            for line in out.move_line_ids_without_package:
                cancel_line_comparation = False
                if (
                    line.product_id.brand_id.id in commissions["product"]["brand"].brands_id.ids
                    and not cancel_line_comparation
                ):
                    if (
                        len(out.commission_images_id) == 1
                        and out.commission_images_id[0].policy_type == "all"
                    ):
                        _logger.warning("==========PICKING: %s", out)
                        _logger.warning("==========COMMISSION: %s", out.commission_images_id)
                        commission_i = out.commission_images_id[0]
                        commission_i.pickings_id -= out
                    commission = commissions["product"]["brand"].filtered(
                        lambda c: line.product_id.brand_id.id in c.brands_id.ids
                    )
                    _logger.warning("==========COMMISSION TO PICK: %s", commission.display_name)
                    _logger.warning("The damn commission: %s" % commission.display_name)
                    commission.get_or_create_commission_image(out, "product", "brand")
                    cancel_line_comparation = True
                if not out.commission_images_id.filtered(lambda x: x.policy_type == "client"):
                    _logger.warning(
                        "==========PICKING: %s",
                        out.commission_images_id.filtered(lambda x: x.policy_type == "client"),
                    )
                    if (
                        out.partner_id.id in commissions["client"].clients_id.ids
                        and not cancel_line_comparation
                    ):
                        commission = commissions["client"].filtered(
                            lambda c: out.partner_id.id in c.clients_id.ids
                        )
                        commission.get_or_create_commission_image(out, "client")
                        cancel_line_comparation = True
                if not out.commission_images_id.filtered(lambda x: x.policy_type == "all"):
                    _logger.warning(
                        "==========PICKING: %s",
                        out.commission_images_id.filtered(lambda x: x.policy_type == "all"),
                    )
                    if not cancel_line_comparation:
                        commissions["all"].get_or_create_commission_image(out, "all")

    def delete_duplicate_outs_in_client_commission(self):
        commission_policy_image = self.env["commission.policy.image"]
        commission_client = commission_policy_image.get_image_commission("client")

        for i, image in enumerate(commission_client):
            if i == 0:
                continue
            _logger.warning(
                "========== PRE-IMAGE A: %s ========== PRE-IMAGE B: %s"
                % (len(image.pickings_id), len(commission_client[i - 1].pickings_id)),
            )
            image.pickings_id -= commission_client[i - 1].pickings_id
            _logger.warning(
                "========== POST-IMAGE A: %s ========== POST-IMAGE B: %s"
                % (len(image.pickings_id), len(commission_client[i - 1].pickings_id)),
            )

    def delete_out_of_invalid_commission(self):
        commission_policy_image = self.env["commission.policy.image"]
        commission_images = {
            "client": commission_policy_image.get_image_commission("client"),
            "all": commission_policy_image.get_image_commission("all"),
        }

        for image in commission_images["client"]:
            outs = self.env["stock.picking"].search(
                [
                    ("create_date", ">=", datetime(2022, 8, 4)),
                    ("create_date", "<", image.create_date),
                    ("picking_type_code", "=", "outgoing"),
                    ("id", "in", image.pickings_id.ids),
                ]
            )
            image.pickings_id -= outs

        duplicate_outs = self.env["stock.picking"].search(
            [
                ("create_date", ">=", datetime(2022, 8, 4)),
                ("picking_type_code", "=", "outgoing"),
                ("id", "in", commission_images["client"].pickings_id.ids),
                ("id", "in", commission_images["all"].pickings_id.ids),
            ]
        )
        _logger.warning("==========DUPLICATES: %s", duplicate_outs)

        for image_all in commission_images["all"]:
            for image_client in commission_images["client"]:
                _logger.warning(
                    "========== PRE-IMAGE A: %s ========== PRE-IMAGE B: %s"
                    % (len(image_all.pickings_id), len(image_client.pickings_id)),
                )
                image_all.pickings_id -= image_client.pickings_id
                _logger.warning(
                    "========== POST-IMAGE A: %s ========== POST-IMAGE B: %s"
                    % (len(image_all.pickings_id), len(image_client.pickings_id)),
                )

        _logger.warning("==========DUPLICATES: %s", duplicate_outs)
