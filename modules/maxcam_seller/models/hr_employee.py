# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployeeMaxcamSeller(models.Model):
    _inherit = 'hr.employee'

    cannot_access_app = fields.Boolean(string='Bloquear acceso a app')
    activate_payment_app = fields.Boolean(string='Activar pagos en app')
    email_personal = fields.Char(string='Correo Personal')
    is_supervisor = fields.Boolean(string='Es Supervisor')
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor', domain=[('is_supervisor', '=', True)])


class HrEmployeePublicMaxcamSeller(models.Model):
    _inherit = 'hr.employee.public'

    cannot_access_app = fields.Boolean(string='Bloquear acceso a app')
    activate_payment_app = fields.Boolean(string='Activar pagos en app')
    journal_id_maxcam = fields.Many2one('account.journal', string='Diario Asociado', tracking=1,domain="[('type', '=','cash')]")
    email_personal = fields.Char(string='Correo Personal')
    is_supervisor = fields.Boolean(string='Supervisor')
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor')