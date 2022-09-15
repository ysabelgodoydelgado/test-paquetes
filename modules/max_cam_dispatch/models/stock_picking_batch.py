# -*- coding: utf-8 -*-
import logging
import string

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockPickingBatchMaxCamDispatch(models.Model):
    _inherit = 'stock.picking.batch'

    # carrier_id = fields.Many2many('delivery.carrier', string='Rutas')
    fleet2_id = fields.Many2one('fleet.vehicle',
                                string='Vehiculo')  # domain=lambda self: [('id', 'in', self._get_vehicle_availables())]
    driver_id = fields.Many2one('hr.employee', string='Chofer',
                                domain=lambda self: [('id', 'in', self._get_driver_availables())])

    

    insurer = fields.Many2one(string='Proveedor', related='fleet2_id.log_contracts.insurer_id', store=True)

    date_open = fields.Date(string='Fecha de emisión')
    date_close = fields.Date(string='Fecha de cierre')

    qty_partners = fields.Integer(string='Cantidad de clientes')
    qty_products = fields.Float(string='Cantidad de productos')

    total_weight = fields.Float(string='Peso Total')

    total_invoice = fields.Float(string='Total')

    is_confirmed = fields.Boolean(string='Confirmado')
    # company currency
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)

    @api.model
    def _get_driver_availables(self):
        """
        Retornar choferes
        :return:
        """
        driver_job = self.env['hr.job'].sudo().search([('name', '=', 'Chofer')], limit=1).id
        user_ids = []
        if driver_job:
            drivers = self.env['hr.employee'].sudo().search([('job_id', '=', driver_job), ('active', '=', True)])
            for s in drivers:
                if not s.id in user_ids:
                    user_ids.append(s.id)
        return user_ids

    @api.depends('company_id', 'picking_type_id', 'state')
    def _compute_allowed_picking_ids(self):
        # agregar ('invoice_ids', '!=',False) para filtrar solo despachos con facturas asociadas
        allowed_picking_states = ['waiting', 'confirmed', 'assigned']#se removio done
        cancelled_batchs = self.env['stock.picking.batch'].search_read(
            [('state', '=', 'cancel')], ['id']
        )
        cancelled_batch_ids = [batch['id'] for batch in cancelled_batchs]

        for batch in self:
            domain_states = list(allowed_picking_states)
            # Allows to add draft pickings only if batch is in draft as well.
            if batch.state == 'draft':
                domain_states.append('draft')
            domain = [
                ('company_id', '=', batch.company_id.id),
                ('immediate_transfer', '=', False),
                ('state', 'in', domain_states),
                '|',
                '|',
                ('batch_id', '=', False),
                ('batch_id', '=', batch.id),
                ('batch_id', 'in', cancelled_batch_ids),
                ('invoice_ids', '!=', False),
                ('state_check', '=',True),
            ]
            if batch.picking_type_id:
                domain += [('picking_type_id', '=', batch.picking_type_id.id)]
            batch.allowed_picking_ids = self.env['stock.picking'].search(domain)

    @api.onchange('picking_ids')
    def _change_picking_ids_venfood(self):
        all_partners = []
        total_weight = 0
        total_qty_products = 0
        exempt = 0
        taxed = 0
        net = 0
        total_i = 0
        for p in self.picking_ids:
            if self.user_id.id != p.partner_id.seller_id.user_id.id:
                raise UserError("Todas las entregas deben ser del mismo vendedor")
            if p.move_ids_without_package:
                for m in p.move_ids_without_package:
                    # reserved_availability es la cantidad reservada
                    if m.product_uom_qty:
                        total_qty_products += m.product_uom_qty

            # lista de diferentes clientes a despachar
            if p.partner_id and p.partner_id.id not in all_partners:
                all_partners.append(
                    p.partner_id.id)  # nota: el partner es direccion de envio, preguntar si se cuenta esto o el padre?

            # numeros de facturas y montos totales acumulados
            invoices_str = ''
            invoices_total = 0
            if len(p.invoice_ids) <= 0:
                raise UserError("No puedes agregar una entrega sin factura asociada")
            for i in p.invoice_ids:
                if i.state in ['posted', 'in_payment', 'paid']:
                    if i.name:
                        invoices_str += str(i.name) + ','
                    # exempt += i.amount_exempt_signed
                    # taxed += i.amount_tax_signed
                    # net += i.amount_untaxed_signed
                    total_i += i.amount_total_signed
            # invoices_total += i.amount_total_signed

        # p.update({'invoice_rel':invoices_str,'invoices_total':invoices_total})
        # 'total_exempt':exempt,'total_taxed':taxed,'total_net':net
        self.update(
            {'qty_partners': len(all_partners), 'total_weight': total_weight, 'qty_products': total_qty_products,
             'total_invoice': total_i})


    """@api.depends('picking_ids', 'picking_ids.state')
    def _compute_state(self):
        batchs = self.filtered(lambda batch: batch.state not in ['cancel', 'done'])
        for batch in batchs:
            if not batch.picking_ids:
                return
            # Cancels automatically the batch picking if all its transfers are cancelled.
            if all(picking.state == 'cancel' for picking in batch.picking_ids):
                batch.state = 'cancel'
            # Batch picking is marked as done if all its not canceled transfers are done.
            #elif all(picking.state in ['cancel', 'done'] for picking in batch.picking_ids):
            #    batch.state = 'done'"""


    """def action_done(self):
        self.ensure_one()
        self._check_company()
        pickings = self.mapped('picking_ids').filtered(lambda picking: picking.state not in ('cancel'))#, 'done'
        if any(picking.state not in ('assigned', 'confirmed','done') for picking in pickings): #done
            raise UserError(_('Some transfers are still waiting for goods. Please check or force their availability before setting this batch to done.'))

        for picking in pickings:
            picking.message_post(
                body="<b>%s:</b> %s <a href=#id=%s&view_type=form&model=stock.picking.batch>%s</a>" % (
                    _("Transferred by"),
                    _("Batch Transfer"),
                    picking.batch_id.id,
                    picking.batch_id.name))
        

        self.state = 'done'
        return pickings.button_validate()"""