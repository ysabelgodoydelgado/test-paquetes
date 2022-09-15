# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_state = fields.Selection([('invoiced', 'Invoiced'), ('2binvoiced', 'To Be Invoiced')], default="2binvoiced",
                                     string="Invoice Control")
    invoice_id = fields.Many2one('account.move')

    def _get_partner_to_invoice(self, picking):
        """ Gets the partner that will be invoiced
            Note that this function is inherited in the sale and purchase modules
            @param picking: object of the picking for which we are selecting the partner to invoice
            @return: object of the partner to invoice
        """
        if picking.sale_id:
            return picking.sale_id.partner_id.id
        elif picking.purchase_id:
            return picking.purchase_id.partner_id.id
        else:
            return picking.partner_id and picking.partner_id.id

    def action_invoice_create(self, journal_id, group=False, move_type='out_invoice'):
        todo = {}
        for picking in self:
            partner = self._get_partner_to_invoice(picking)
            # grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id
            # for move in picking.move_lines:
            for move in picking.move_line_ids:
                # _logger.info("este  es el picking_id de la linea de move_lines %s",picking_id)
                check_in = self.validate_check_in(picking)
                print("check_in", check_in)
                print("move.picking_id.invoice_state", move.picking_id.invoice_state)
                if move.picking_id.invoice_state == '2binvoiced' or check_in:
                    if (move.state != 'cancel') and not move.move_id.scrapped:
                        todo.setdefault(key, [])
                        todo[key].append(move)
        invoices = []
        for moves in todo.values():
            _logger.info("este es el moves de primeroooooooooo %s", moves)
            invoices += self._invoice_create_line(moves, journal_id, move_type)

        return invoices

    def validate_check_in(self, picking):
        invoice_draft = picking.invoice_ids.filtered(lambda l: l.state in ['draft', 'cancel'])
        invoice_posted = picking.invoice_ids.filtered(lambda l: l.state == 'posted')
        if invoice_posted:
            # facturas publicadas
            flag = False
        elif len(invoice_draft) > 0:
            # facturas borrador o canceladas
            flag = True
        else:
            # sin factura
            flag = True
        return flag

    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        partner, currency_id, company_id, user_id = key
        if inv_type in ('out_invoice'):
            account_id = partner.property_account_receivable_id.id
            payment_term = partner.property_payment_term_id.id or False
        else:
            account_id = partner.property_account_payable_id.id
            payment_term = partner.property_supplier_payment_term_id.id or False

        if move.move_id.purchase_line_id and move.move_id.purchase_line_id.order_id:
            purchase = move.move_id.purchase_line_id.order_id
            payment_term = purchase.payment_term_id.id

        sale = move.picking_id.sale_id

        inv_vals = {
            'ref': move.picking_id.name,
            'invoice_date': fields.Date.context_today(self),
            'user_id': user_id,
            'partner_id': partner.id,
            'move_type': inv_type,
            'company_id': company_id,
            'currency_id': currency_id,
            'journal_id': journal_id,
        }
        if sale and inv_type in ('out_invoice'):
            inv_vals.update({
                'invoice_payment_term_id': sale.payment_term_id.id,
                'user_id': sale.user_id.id,
                'invoice_user_id': sale.user_id.id,
                'team_id': sale.team_id.id,
                'invoice_origin': sale.name,

                'narration': sale.note,
                'partner_shipping_id': sale.partner_shipping_id.id,
                'can_send_to_admin':sale.can_send_to_admin,

            })
        return inv_vals

    def _create_invoice_from_picking(self, picking, vals):
        ''' This function simply creates the invoice from the given values. It is overriden in delivery module to add the delivery costs.
        '''
        invoice_obj = self.env['account.move']
        return invoice_obj.with_context(default_move_type='out_invoice').create(vals)

    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        invoice_obj = self.env['account.move']
        move_obj = self.env['stock.move']
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(moves, inv_type)
        product_price_unit = {}
        invoice_id = False

        for move in moves:
            _logger.info("ESTE ES EL MOVEEEE en el for %s", move)
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(move, company)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(key, inv_type, journal_id, move)
            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(move.picking_id, invoice_vals)
                invoice_id.picking_ids = [(4, move.picking_id.id)]
                invoices[key] = invoice_id.id
            else:
                invoice = invoice_obj.browse(invoices[key])
                invoice.picking_ids = [(4, move.picking_id.id)]
                merge_vals = {}
                if not invoice.ref or invoice_vals['ref'] not in invoice.ref.split(', '):
                    invoice_origin = filter(None, [invoice.ref, invoice_vals['ref']])
                    merge_vals['ref'] = ', '.join(invoice_origin)
                if invoice_vals.get('name', False) and (
                        not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
                    invoice_name = filter(None, [invoice.name, invoice_vals['name']])
                    merge_vals['name'] = ', '.join(invoice_name)
                if merge_vals:
                    invoice.write(merge_vals)

            invoice_line_vals = move_obj._get_invoice_line_vals(move, partner, inv_type)
            invoice_line_vals['move_id'] = invoices[key]
            invoice_line_vals['ref'] = origin
            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals['product_id']] = invoice_line_vals['price_unit']
            if is_extra_move[move.id] and (invoice_line_vals['product_id']) in product_price_unit:
                invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id']]
            if is_extra_move[move.id]:
                desc = (inv_type in ('out_invoice') and move.product_id.product_tmpl_id.description_sale) or \
                       (inv_type in ('purchase') and move.product_id.product_tmpl_id.description_purchase)
                invoice_line_vals['name'] += ' ' + desc if desc else ''
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
                # the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]
            invice_line = invoice_id.update({
                'invoice_line_ids': [(0, None, invoice_line_vals)]
            })
            move_data = self.env['account.move'].browse(invoices[key])

            move.picking_id.write({'invoice_state': 'invoiced', 'invoice_id': invoice_id.id})

        if invoice_id:
            if self.sale_id:
                # account_id
                vals_flet = False
                discount = 0.0
                account_id = self.partner_id.property_delivery_carrier_id.product_id.property_account_income_id.id
                # if not account_id:
                #     account_id = move.product_id.categ_id.property_account_income_categ_id.id
                product_id = self.partner_id.property_delivery_carrier_id.product_id.id
                quantity = 1
                ref = self.origin
                #
                if ref:
                    order = self.env['sale.order'].search([('name', '=', ref)], limit=1)
                    if order:
                        price_unit = self.partner_id.property_delivery_carrier_id._get_price_available_inv(
                            invoice_id, order.amount_total)
                        # price_unit = self.partner_id.property_delivery_carrier_id._get_price_available(order)
                        vals_flet = {'discount': discount, 'account_id': account_id, 'product_id': product_id,
                                     'quantity': quantity, 'ref': ref, 'price_unit': price_unit}
                # No se sabe porque invoice_id se declara como Falso pero cosas raras pasan by Antony H.
                if vals_flet:
                    invoice_id.update({
                        'invoice_line_ids': [(0, None, vals_flet)]
                    })

            invoice_id._compute_amount()
            if not invoice_id.is_purchase_document(include_receipts=True):
                invoice_id._post()

        for inv_line in invoice_id.invoice_line_ids:
            for move in moves:

                if inv_line.product_id.id == move.product_id.id:
                    if move.move_id.sale_line_id:
                        move.move_id.sale_line_id.invoice_lines = [(4, inv_line.id)]

                    if move.move_id.purchase_line_id:
                        move.move_id.purchase_line_id.invoice_lines = [(4, inv_line.id)]

        return invoices.values()


class stock_move(models.Model):
    _inherit = 'stock.move'

    def _get_moves_taxes(self, moves, inv_type):
        # extra moves with the same picking_id and product_id of a move have the same taxes
        extra_move_tax = {}
        is_extra_move = {}
        for move in moves:
            if move.picking_id:
                is_extra_move[move.id] = True
                if not (move.picking_id, move.product_id) in extra_move_tax:
                    extra_move_tax[move.picking_id, move.product_id] = 0
            else:
                is_extra_move[move.id] = False
        return (is_extra_move, extra_move_tax)

    def _get_master_data(self, move, company):
        ''' returns a tuple (browse_record(res.partner), ID(res.users), ID(res.currency)'''
        currency = company.currency_id.id
        if move.picking_id.sale_id:

            partner = move.picking_id.sale_id.partner_id
        elif move.picking_id.purchase_id:
            partner = move.picking_id.purchase_id.partner_id
        else:
            partner = move.picking_id and move.picking_id.partner_id

        if partner:
            code = self.get_code_from_locs(move)
            if partner.property_product_pricelist and code == 'outgoing':
                currency = partner.property_product_pricelist.currency_id.id
        return partner, self._uid, currency

    def get_code_from_locs(self, move, location_id=False, location_dest_id=False):
        code = 'internal'
        src_loc = location_id or move.location_id
        dest_loc = location_dest_id or move.location_dest_id
        if src_loc.usage == 'internal' and dest_loc.usage != 'internal':
            code = 'outgoing'
        if src_loc.usage != 'internal' and dest_loc.usage == 'internal':
            code = 'incoming'
        return code

    def _get_taxes(self, move):
        if move.move_id.purchase_line_id.taxes_id:
            return [tax.id for tax in move.move_id.purchase_line_id.taxes_id]
        if move.move_id.sale_line_id.tax_id:
            return [tax.id for tax in move.move_id.sale_line_id.tax_id]
        return []

    def _get_price_unit_invoice(self, move_line, move_type):
        if move_type in ('in_invoice', 'in_refund'):
            return move_line.move_id.price_unit
        else:
            price = move_line.move_id.sale_line_id.price_unit
            if price:
                return price

    def _get_invoice_line_vals(self, move, partner, inv_type):
        name = False
        move_lies = []
        # for move in moves:
        if inv_type in ('out_invoice'):
            account_id = move.product_id.property_account_income_id.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_income_categ_id.id
            if move.move_id.sale_line_id:
                name = move.move_id.sale_line_id.name
        else:
            account_id = move.product_id.property_account_expense_id.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_expense_categ_id.id

        # set UoS if it's a sale and the picking doesn't have one
        # uos_id = move.product_uom.id
        uos_id = move.product_uom_id.id

        # quantity = move.product_uom_qty
        _logger.info("Este es el moveeeeeeeeeeee %s", move)
        quantity = move.qty_check

        taxes_ids = self._get_taxes(move)
        if self._get_price_unit_invoice(move, inv_type) != None:
            price = self._get_price_unit_invoice(move, inv_type)
            subtotal = quantity * self._get_price_unit_invoice(move, inv_type)
        else:
            price = 0.0
            subtotal = quantity
        return {
            'name': name or move.move_id.name,
            'move_id': move.id,
            'account_id': account_id,
            'product_id': move.product_id.id,
            'quantity': quantity,
            'price_subtotal': subtotal,
            'price_unit': price,
            'tax_ids': [(6, 0, taxes_ids)],
            'discount': move.move_id.sale_line_id.discount,
            'analytic_account_id': move.move_id.sale_line_id.order_id.analytic_account_id.id or False,
            'product_uom_id': uos_id,
        }
