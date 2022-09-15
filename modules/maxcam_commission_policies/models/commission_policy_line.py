import logging

from odoo import api, _
from odoo.exceptions import ValidationError
from odoo.fields import (
    Boolean,
    Float,
    Integer,
    Many2one,
)
from odoo.models import Model
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class CommissionPolicyLine(Model):
    _name = "commission.policy.line"
    _description = "Commission percentage based in a certain range date"

    date_from = Integer("Desde", required=True, default=1, help="From days")
    date_until = Integer("Hasta", required=True, help="until days")
    commission = Float("Comisión", required=True, help="Commission percentage")
    percentage_report = Float("Porcentaje para Reportes", help="Commission percentage of reports")
    not_applied = Boolean(
        "No Aplicar para Reporte", help="Do not apply this restriction to the report"
    )
    policy_id = Many2one(
        "commission.policy", string="Politica de Comisiones", required=True, ondelete="cascade"
    )

    @api.constrains("commission")
    def _check_commission_non_negative(self):
        for commission_line in self:
            if float_compare(commission_line.commission, 0.0, precision_digits=2) < 0:
                raise ValidationError(_("¡La comisión no puede ser menor a cero!"))
