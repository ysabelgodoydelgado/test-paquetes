# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class Client_ret(models.Model):
    _inherit = 'res.partner'

    def _get_configurate_supplier_islr_retention(self):
        search = self.env['retention_venezuela.configurate'].search([('code', '=', 'retention')])
        if search:
            return search.account_retention_islr.id

    def _get_configurate_supplier_iva_retention(self):
        search = self.env['retention_venezuela.configurate'].search([('code', '=', 'retention')])
        if search:
            return search.account_retention_iva.id

    withholding_type = fields.Many2one('retention_venezuela.withholdings', 'Tipo de retención', domain="[('status','=',True)]", required=False)
    iva_retention = fields.Many2one('account.account', 'Retención de IVA')
    islr_retention = fields.Many2one('account.account', 'Retención de ISLR')
    taxpayer = fields.Selection([('formal', 'Formal'), ('special', 'Especial'), ('ordinary', 'Ordinario')], string='Tipo de contribuyente', default='ordinary')
    type_person_ids = fields.Many2one('master.type_person', 'Tipo de Persona')

    supplier_iva_retention = fields.Many2one('account.account', 'Retención de IVA  para proveedor', default=_get_configurate_supplier_iva_retention, readonly=1)
    supplier_islr_retention = fields.Many2one('account.account', 'Retención de ISLR para proveedor', default=_get_configurate_supplier_islr_retention, readonly=1)
    exempt_islr = fields.Boolean(default=True, string='Excento ISLR', help='Indica si es exento de retencion de ISLR')
    exempt_iva = fields.Boolean(default=True, string='Excento IVA', help='Indica si es exento de retencion de IVA')
