# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from . import validations
import datetime


class Configurate(models.Model):
    _name = "retention_venezuela.configurate"
    _description = "Configuraciones generales"

    name = fields.Char(string='Descripción', required=True)
    code = fields.Char(string='Código', required=True, default="retention", readonly=True)

    company_id = fields.Many2one('res.company', 'Compañia', required=True)
    account_retention_iva = fields.Many2one('account.account', 'Cuenta de Retención IVA', required=True)
    account_retention_islr = fields.Many2one('account.account', 'Cuenta de Retención ISLR', required=True)

    account_retention_receivable_client = fields.Many2one('account.account', 'Cuenta P/cobrar clientes', required=True)
    account_retention_to_pay_supplier = fields.Many2one('account.account', 'Cuenta P/pagar proveedor', required=True)

    journal_retention_client = fields.Many2one('account.journal', 'Libro de Retenciones de Clientes', required=True)
    journal_retention_supplier = fields.Many2one('account.journal', 'Libro de Retenciones de Proveedores', required=True)

    status = fields.Boolean(default=True, string="Activo")

    _sql_constraints = [('company_id_unique', 'unique(company_id)', 'Ya existe una configuracion para esta compañia')]
