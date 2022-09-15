# -*- coding: utf-8 -*-
import logging

import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from pprint import pprint

_logger = logging.getLogger(__name__)


class MaxcamAccountMove(models.Model):
    _inherit = 'account.move'

    foreign_currency_id = fields.Many2one('res.currency', string="Moneda/Divisa",
                                          default=lambda self: self.env.ref("base.VEF"))
    foreign_currency_rate = fields.Float(string='Tasa Divisa', digits=(12, 2),
                                         default=lambda self: self.compute_foreign_rate(),
                                         help='Guarda la tasa en que se calcula el total en la moneda foránea')

    sent_to_admin = fields.Boolean(string='Enviada a administración', default=False)

    can_send_to_admin = fields.Boolean(string='Enviada a administración', default=False)

    # def action_invoice_sent(self):
    #     res = super(MaxcamAccountMove, self).action_invoice_sent()
    #     template = self.env.ref('maxcam_account.maxcam_invoice_free_form_template', raise_if_not_found=False)
    #     res.get('context').update({'default_use_template': False, 'default_template_id': template.id})
    #     pprint(res)
    #     return res

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        res = super(MaxcamAccountMove, self).action_invoice_print()
        return self.env.ref('maxcam_account.invoice_free_form_1_id').report_action(self)

    def send_to_admin(self):
        _logger.info("enviar a admin")
        self.ensure_one()

        # raw_data = self.read()
        # _logger.info("RAW DATAAAAAAAAAA %s",raw_data)
        tasa = self.foreign_currency_rate if self.foreign_currency_rate else 1
        try:
            data = {"jsonrpc": "2.0", "params":
                {'name': self.name, 'date': self.date.strftime("%d/%m/%Y"), 'state': self.state,
                 'move_type': self.move_type, 'journal_id_code': self.journal_id.code,
                 'payment_reference': self.payment_reference, 'amount_untaxed': self.amount_untaxed * tasa,
                 'amount_tax': self.amount_tax * tasa, 'amount_total': self.amount_total * tasa,
                 'amount_residual': self.amount_residual * tasa,
                 'payment_state': self.payment_state, 'invoice_date': self.invoice_date.strftime("%d/%m/%Y"),
                 'invoice_date_due': self.invoice_date_due.strftime("%d/%m/%Y"),
                 'invoice_origin': self.invoice_origin, 'invoice_payment_term_name': self.invoice_payment_term_id.name,
                 'partner_vat': self.partner_id.vat, 'seller_id_name': self.seller_id.name if self.seller_id else False,
                 'invoice_line_ids': self.get_invoice_lines(self.invoice_line_ids),
                 'rate': tasa,
                 },
                    }
            _logger.info("data a enviaraaaaaaaaaaaaaaaaa %s", data)
            url_base = self.env['ir.config_parameter'].sudo().get_param('url_admin_contable')
            if not url_base:
                raise UserError("No hay url configurada para conectar con Administracion")
            url_admin = url_base + "/admin/load_invoice_from_erp/"
            _logger.info("url a contactar --------------------------%s", url_admin)
            headers = {'content-type': 'application/json', 'accept': 'application/json'}
            req = requests.post(url_admin, headers=headers, json=data)
            response = req.json()
            _logger.info("Respuesta obtenida de sistema administrativo %s", response)
            success = False
            msg = ''
            if response and response.get('result', False):
                r = response.get('result')
                if len(r) == 2:
                    success = r[0]
                    if success:
                        # marcar como enviada a administracion
                        self.sent_to_admin = True
                    msg = r[1]
            _logger.info("mostrar el mensaje %s", msg)

            return {
                'name': 'información',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('maxcam_account.wizard_message_max_cam_invoice_send').id,
                'res_model': 'wizard.message.maxcam.invoice.send',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_msg': msg,
                },
            }
        except Exception as e:
            _logger.info("EXepcion %s", e)
            raise UserError(
                "Ocurrio un error y no se pudo completar el registro en administración,verifique su conexión")

    def get_invoice_lines(self, lines):
        il = []
        for l in lines:
            tasa = l.move_id.foreign_currency_rate if l.move_id.foreign_currency_rate else 1
            price_unit = l.price_unit * tasa
            price_subtotal = l.price_unit * tasa
            price_total = l.price_unit * tasa
            tax_id = l.tax_ids[0].amount if len(l.tax_ids) > 0 else 0
            if tax_id == 0:
                tax_id = False
            lo = {'product_code': l.product_id.default_code, 'product_name': l.product_id.name,
                  'alternate_code': l.product_id.alternate_code, 'product_uom_name': l.product_uom_id.name,
                  'name': l.name, 'quantity': l.quantity,
                  'price_unit': price_unit, 'price_subtotal': price_subtotal, 'price_total': price_total,
                  'discount': l.discount, 'tax_id': tax_id,
                  'brand_name': l.product_id.brand_id.name if l.product_id.brand_id else False}
            il.append(lo)
        return il

    def get_last_rate(self, rate_ids, date_invoice=False):
        domain_rate = [('id', 'in', rate_ids)]
        if date_invoice:
            domain_date = [('name', '=', date_invoice)]
            domain = domain_rate + domain_date
            rate = self.env['res.currency.rate'].sudo().search(domain, order='write_date desc', limit=1)
            _logger.info("SI eencontro rate %s", rate)
            if not rate:
                rate = self.env['res.currency.rate'].sudo().search(domain_rate, order='name desc, write_date desc',
                                                                   limit=1)
        else:
            rate = self.env['res.currency.rate'].sudo().search(domain_rate,
                                                               order='name desc, write_date desc', limit=1)
        return rate

    @api.onchange('invoice_date')
    def compute_foreign_rate(self):
        if not self:
            rate_ids = self.env.ref("base.VEF").rate_ids.ids
            if rate_ids:
                rate = self.env['account.move'].get_last_rate(rate_ids, fields.Date.today())
                if len(rate) > 0:
                    return round(rate.rate, 4)
            else:
                return 0

        for record in self:
            rate_ids = record.foreign_currency_id.rate_ids.ids if record.foreign_currency_id else False
            if record.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'] and rate_ids:
                rate = record.get_last_rate(rate_ids, record.invoice_date)
                if len(rate) > 0:
                    record.foreign_currency_rate = round(rate.rate, 4)

    @api.constrains('amount_total')
    def _onchange_limit_credit(self):
        for record in self:
            record.ensure_one()
            if record.move_type == 'out_invoice' and record.state == 'draft' and record.partner_id.credit_limit > 0:
                due = record.partner_id.total_due + record.amount_total
                if due > record.partner_id.credit_limit:
                    raise UserError(_("El cliente no tiene Límite de Crédito disponible"))

    def action_reverse(self):
        for record in self:
            pk_in = record.picking_ids.filtered(lambda pk: pk.picking_type_code == 'incoming')
            if len(pk_in) == 0 and not self.env.user.has_group('base.group_system'):
                #no hay devolucion y No es admin
                raise UserError(_("No puedes emitir una nota de crédito si no hay devolución asociada"))
        res = super(MaxcamAccountMove, self).action_reverse()
        return res


class WizardMessageMaxCamSendInvoiceAdmin(models.TransientModel):
    _name = "wizard.message.maxcam.invoice.send"
    _description = "Mensaje Confirmacion"

    msg = fields.Char(string='Mensaje')

    def button_confirm_alert(self):
        pass
