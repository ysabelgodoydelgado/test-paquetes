from odoo import models, fields, api, exceptions
from collections import OrderedDict
import pandas as pd
import logging

_logger = logging.getLogger(__name__)


class EfectividadVendedores(models.TransientModel):
    _inherit = 'wizard.reportes.comision'

    def _efectividad(self, wizard=False):
        if wizard:
            wiz = self.search([('id', '=', wizard)])
        else:
            wiz = self
        search_domain = wiz._get_domain()
        docs = self.env['account.move'].search(search_domain)
        partner_ids = wiz.env['res.partner'].search([('parent_id','=',False)])
        user_ids = wiz.env['hr.employee'].search([])
        dic = OrderedDict([
            ('Vendedor', ''),
            ('Cant. Clientes', 0),
            ('Cant. Clientes Facturados', 0),
            ('Efectividad', 0.00),
        ])
        lista = []
        for u in user_ids:
            inv_p = []
            for inv in docs.filtered(lambda i: i.seller_id.id == u.id):
                if inv.partner_id.id not in inv_p:
                    inv_p.append(inv.partner_id.id)
            len_i = len(inv_p)
            len_p = len(partner_ids.filtered(lambda p: p.seller_id.id == u.id))
            dicti = OrderedDict()
            dicti.update(dic)
            dicti['Vendedor'] = u.name
            dicti['Cant. Clientes'] = len_p
            dicti['Cant. Clientes Facturados'] = len_i
            dicti['Efectividad'] = (len_i/len_p) if len_p > 0 else 0
            lista.append(dicti)
        tabla = pd.DataFrame(lista)
        return tabla.fillna(0)
