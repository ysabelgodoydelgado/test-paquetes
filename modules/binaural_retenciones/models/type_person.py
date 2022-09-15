# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class TypePerson(models.Model):
    _name = "master.type_person"
    _description = "Tipo de Persona"

    name = fields.Char(string='Descripcion', required=True)
    status = fields.Boolean(default=True, string="Activo")
