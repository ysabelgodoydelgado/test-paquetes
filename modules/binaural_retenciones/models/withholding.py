# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re
from . import validations


class WithHoldings(models.Model):
    _name = 'retention_venezuela.withholdings'
    _order = 'create_date desc'
    _desc = 'Retenciones de IVA'
    _sql_constraints = [('unique_name', 'UNIQUE(name)', 'No puedes agregar retenciones con el mismo nombre')]
    name = fields.Char(string="Nombre", required=True)
    value = fields.Float(string="Valor", required=True)
    status = fields.Boolean(default=True, string="Activo")

    @api.onchange('name')
    def upper_name(self):
        return validations.case_upper(self.name, "name")

    @api.onchange('value')
    def onchange_template_id(self):
        res = {}
        if self.value:
            res = {'warning': {
                'title': ('Advertencia'),
                'message': ('Recuerda usar coma (,) como separador de decimales')
                }
            }

        if res:
            return res
