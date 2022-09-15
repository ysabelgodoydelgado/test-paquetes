import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class CommissionPolicyImageLine(models.Model):
    _name = "commission.policy.image.line"
    _description = "Image of the exact moment when a date range is requested or modified."

    date_from = fields.Integer("Desde", required=True, default=1, help="From days")
    date_until = fields.Integer("Hasta", required=True, help="until days")
    commission = fields.Float("Comisión", required=True, help="Commission percentage")
    percentage_report = fields.Float(
        "Porcentaje para Reportes", help="Commission percentage of reports"
    )
    not_applied = fields.Boolean(
        "No Aplicar para Reporte", help="Do not apply this restriction to the report"
    )
    policy_image_id = fields.Many2one(
        "commission.policy.image",
        string="Historico de Comisiones",
        required=True,
        ondelete="cascade",
    )
