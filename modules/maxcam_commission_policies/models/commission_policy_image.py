import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CommissionPolicyImage(models.Model):
    _name = "commission.policy.image"
    _description = "A backup image of the moment when a commission is requested or modified."
    _order = "create_date desc"

    name = fields.Char(string="Nombre", required=True)
    date_created = fields.Datetime(string="Fecha de Creación", required=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    policy_type = fields.Selection(
        selection=[("client", "Cliente"), ("product", "Producto"), ("all", "General")],
        string="Tipo de Comisión",
        required=True,
    )
    product_commission_type = fields.Selection(
        selection=[("product", "Producto"), ("category", "Categoría"), ("brand", "Marca")],
        string="Aplicar A",
    )
    is_report_range = fields.Boolean("Rango de Reportes", groups="base.group_no_one", copy=False)

    pickings_id = fields.Many2many(
        "stock.picking", "commission_policy_image_picking_rel", string="Albaranes"
    )
    clients_id = fields.Many2many(
        "res.partner", "commission_policy_image_client_rel", string="Clientes VIP"
    )
    products_id = fields.Many2many(
        "product.product", "commission_policy_image_product_rel", string="Productos"
    )
    brands_id = fields.Many2many(
        "product.brand", "commission_policy_image_brand_rel", string="Marcas"
    )
    categories_id = fields.Many2many(
        "product.category", "commission_policy_image_category_rel", string="Categorías"
    )
    commission_line_ids = fields.One2many(
        "commission.policy.image.line", "policy_image_id", string="Rango de Comisiones"
    )
    product_ids = fields.One2many("product.product", "commission_policy_image_id")

    @api.depends("policy_type", "name")
    def _compute_display_name(self):
        policy_type_dict = {"client": "Cliente", "product": "Producto", "all": "General"}
        for commission_i in self:
            commission_i.display_name = (
                f"{policy_type_dict.get(commission_i.policy_type)} ({commission_i.name})"
            )

    @api.model
    def get_image_commission(self, policy_type: str, product_policy_type=None):
        """
        Method to get the last image of a commission policy.

        :param policy_type: The type of commission policy.
        :param product_policy_type: The type of product policy.
        :return: recordset of the last image of a commission policy found in given types.
        """

        commission_policy = None
        if product_policy_type:
            commission_policy = self.env["commission.policy.image"].search(
                [
                    ("policy_type", "=", policy_type),
                    ("product_commission_type", "=", product_policy_type),
                ],
            )
        else:
            commission_policy = self.env["commission.policy.image"].search(
                [("policy_type", "=", policy_type)]
            )

        return commission_policy

    @api.model
    def is_commission_in_type(self, o_commission):
        for commission_i in self:
            if commission_i.compare_commission_image(o_commission):
                return commission_i

        return False

    @api.model
    def compare_commission_image(self, o_commission) -> bool:
        """
        Compare the current commission image with its original commission.

        :param o_commission: commission to compare with current image
        :return True if the commissions are the same, False otherwise.
        """

        attr_equally_list = []

        if self.products_id:
            attr_equally_list.append(self.products_id.ids == o_commission.products_id.ids)
        if self.brands_id:
            attr_equally_list.append(self.brands_id.ids == o_commission.brands_id.ids)
        if self.categories_id:
            attr_equally_list.append(self.categories_id.ids == o_commission.categories_id.ids)
        if self.clients_id:
            attr_equally_list.append(self.clients_id.ids == o_commission.clients_id.ids)
        if self.product_ids:
            attr_equally_list.append(self.product_ids.ids == o_commission.product_ids.ids)

        for policy_line, i_policy_line in zip(
            self.commission_line_ids, o_commission.commission_line_ids
        ):
            attr_equally_list.append(
                policy_line.date_from == i_policy_line.date_from
                and policy_line.date_until == i_policy_line.date_until
                and policy_line.commission == i_policy_line.commission
            )

        return all(attr_equally_list)
