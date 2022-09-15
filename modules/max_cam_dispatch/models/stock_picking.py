# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round

_logger = logging.getLogger(__name__)

from odoo.tools.misc import OrderedSet

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]


class MaxcamstockPickingDispatch(models.Model):
    _inherit = 'stock.picking'

    invoice_rel = fields.Char(string='Facturas', default='', compute='invoices_relation')
    invoices_total_amount = fields.Float(string='Total de facturas', compute='invoices_relation')
    # company currency
    date_reception_client = fields.Date(string='Fecha de recepción')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    # qty_packages_dispatch_total = fields.Float(string='Total de bultos de la entrega',
    # compute='recalculate_total_qty_packages')
    qty_packages_dispatch_total = fields.Integer(string='Total de bultos de la entrega')

    verify_zero = fields.Boolean(string='Verificado cantidades 0')

    state_check = fields.Boolean(string='Chequeado', default=False)

    def do_print_picking(self):
        self.write({'printed': True})
        # return self.env.ref('stock.action_report_picking').report_action(self)
        return self.env.ref('stock.action_report_delivery').report_action(self)

    def action_check_maxcam(self):
        if self.state_check:
            self.state_check = False
            self.verify_zero = False
            for l in self.move_line_ids:
                if l.qty_check > l.product_uom_qty:
                    raise UserError("Cantidad chequeada no puede ser mayor a reservada")
                else:
                    l.product_id.sudo().qty_on_hand_checked -= l.qty_check
        else:
            qty_lines = len(self.move_line_ids)
            qty_zero = len(self.move_line_ids.filtered(lambda r: r.qty_check == 0))
            if qty_lines == qty_zero and not self.verify_zero:
                # all lines in 0 return popup
                return {
                    'name': 'Advertencia',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('max_cam_dispatch.wizard_message_venfood_view_check_confirm').id,
                    'res_model': 'wizard.message.verify.zero',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_picking_id': self.id,
                        'default_name_modal_message': '¿Todas las cantidades a chequear estan en 0, esta seguro de chequear?'
                    },
                }
            self.state_check = True
            for l in self.move_line_ids:
                if l.qty_check > l.product_uom_qty:
                    raise UserError("Cantidad chequeada no puede ser mayor a reservada")
                else:
                    l.product_id.sudo().qty_on_hand_checked += l.qty_check

    def _action_done(self):
        """Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()
        _logger.info("self antes de todo %s", self)

        todo_moves = self.mapped('move_lines').filtered(
            lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed',
                                        'done'])  # agregado done
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': fields.Datetime.now(), 'priority': '0'})
        for p in self:
            if p.picking_type_id.code == 'outgoing':
                for i in p.invoice_ids:
                    date = p.date_reception_client if p.date_reception_client else fields.Date.today()
                    if not p.date_reception_client:
                        p.write({'date_reception_client': date})
                    i.write({'reception_date_client': date})
                    i.recompute_invoice_due_date()

        # if incoming moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(
            lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True

    # @api.depends('invoice_ids.qty_packages')
    # def recalculate_total_qty_packages(self):
    #     for record in self:
    #         if record.invoice_ids:
    #             record.qty_packages_dispatch_total = sum(line.qty_packages for line in record.invoice_ids)
    #         else:
    #             record.qty_packages_dispatch_total = 0

    @api.depends('invoice_ids')
    def invoices_relation(self):
        for record in self:
            invoices_str = ''
            total_by_picking = 0
            for i in record.invoice_ids:
                if i.state in ['posted']:
                    if i.name:
                        invoices_str += str(i.name) + ','
                    if i.amount_total_signed:
                        total_by_picking += i.amount_total_signed

            record.invoice_rel = invoices_str
            record.invoices_total_amount = total_by_picking

    def action_print_delivery_slip_from_as(self):
        for p in self:
            p.do_print_picking()

    """def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('cancel'))) #'done', 
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
        return True"""


class MaxcamstockMove(models.Model):
    _inherit = 'stock.move'
    qty_check = fields.Float(string='Check', digits='Product Unit of Measure', copy=False, default=0.0)


class MaxcamstockMoveLines(models.Model):
    _inherit = 'stock.move.line'

    qty_check = fields.Float(string='Check', digits='Product Unit of Measure', copy=False, default=0.0)
    state_check = fields.Boolean(string='Chequeado', related='picking_id.state_check')

    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_tracked_without_lot = OrderedSet()
        ml_ids_to_delete = OrderedSet()
        ml_ids_to_create_lot = OrderedSet()
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (
                ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name:
                                if ml.product_id.tracking == 'lot' and not ml.lot_id:
                                    lot = self.env['stock.production.lot'].search([
                                        ('company_id', '=', ml.company_id.id),
                                        ('product_id', '=', ml.product_id.id),
                                        ('name', '=', ml.lot_name),
                                    ], limit=1)
                                    if lot:
                                        ml.lot_id = lot.id
                                    else:
                                        ml_ids_to_create_lot.add(ml.id)
                                else:
                                    ml_ids_to_create_lot.add(ml.id)
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id and ml.id not in ml_ids_to_create_lot:
                        ml_ids_tracked_without_lot.add(ml.id)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_ids_to_delete.add(ml.id)

        if ml_ids_tracked_without_lot:
            mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
            raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
                            '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))
        ml_to_create_lot = self.env['stock.move.line'].browse(ml_ids_to_create_lot)
        ml_to_create_lot._create_and_assign_production_lot()

        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()

        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()

        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        for ml in mls_todo:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty,
                                                                                       precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id,
                                                                               rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id,
                                         package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
                # unreserve what's been reserved
                if not ml._should_bypass_reservation(
                        ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id,
                                                    package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                _logger.info("MOVE LINE EN ACTION DONE DEL MOVE LINE %s", ml)
                if ml.picking_id and ml.picking_id.picking_type_id.code == 'outgoing' and ml.state_check:
                    ml.product_id.sudo().qty_on_hand_checked -= ml.qty_check

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                               rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                          lot_id=ml.lot_id, package_id=ml.package_id,
                                                                          owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                  package_id=ml.package_id, owner_id=ml.owner_id,
                                                                  strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                         lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                         lot_id=ml.lot_id, package_id=ml.package_id,
                                                         owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                 package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            ml_ids_to_ignore.add(ml.id)
        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('move_id'):
                vals['company_id'] = self.env['stock.move'].browse(vals['move_id']).company_id.id
            elif vals.get('picking_id'):
                vals['company_id'] = self.env['stock.picking'].browse(vals['picking_id']).company_id.id
            if vals.get('product_uom_qty', False):
                vals['qty_check'] = vals.get('product_uom_qty')

        mls = super().create(vals_list)

        def create_move(move_line):
            new_move = self.env['stock.move'].create({
                'name': _('New Move:') + move_line.product_id.display_name,
                'product_id': move_line.product_id.id,
                'product_uom_qty': 0 if move_line.picking_id and move_line.picking_id.state != 'done' else move_line.qty_done,
                'product_uom': move_line.product_uom_id.id,
                'description_picking': move_line.description_picking,
                'location_id': move_line.picking_id.location_id.id,
                'location_dest_id': move_line.picking_id.location_dest_id.id,
                'picking_id': move_line.picking_id.id,
                'state': move_line.picking_id.state,
                'picking_type_id': move_line.picking_id.picking_type_id.id,
                'restrict_partner_id': move_line.picking_id.owner_id.id,
                'company_id': move_line.picking_id.company_id.id,
            })
            move_line.move_id = new_move.id

        # If the move line is directly create on the picking view.
        # If this picking is already done we should generate an
        # associated done move.
        for move_line in mls:
            if move_line.move_id or not move_line.picking_id:
                continue
            if move_line.picking_id.state != 'done':
                moves = move_line.picking_id.move_lines.filtered(lambda x: x.product_id == move_line.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    move_line.move_id = moves[0].id
                else:
                    create_move(move_line)
            else:
                create_move(move_line)

        for ml, vals in zip(mls, vals_list):
            if ml.move_id and \
                    ml.move_id.picking_id and \
                    ml.move_id.picking_id.immediate_transfer and \
                    ml.move_id.state != 'done' and \
                    'qty_done' in vals:
                ml.move_id.product_uom_qty = ml.move_id.quantity_done
            if ml.state == 'done':
                if 'qty_done' in vals:
                    ml.move_id.product_uom_qty = ml.move_id.quantity_done
                if ml.product_id.type == 'product':
                    Quant = self.env['stock.quant']
                    quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                                   rounding_method='HALF-UP')
                    in_date = None
                    available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                              lot_id=ml.lot_id,
                                                                              package_id=ml.package_id,
                                                                              owner_id=ml.owner_id)
                    if available_qty < 0 and ml.lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                      package_id=ml.package_id, owner_id=ml.owner_id,
                                                                      strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                            Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                             lot_id=False, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                            Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                             lot_id=ml.lot_id, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                    Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                     package_id=ml.result_package_id, owner_id=ml.owner_id,
                                                     in_date=in_date)
                next_moves = ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
                next_moves._do_unreserve()
                next_moves._action_assign()
        return mls


class StockImmediateTransferMaxCamInh(models.TransientModel):
    _inherit = 'stock.immediate.transfer'
    _description = 'Immediate Transfer'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.immediate_transfer_line_ids:
            if line.to_immediate is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for picking in pickings_to_do:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    # move_line.qty_done = move_line.product_uom_qty
                    move_line.qty_done = move_line.qty_check
                    # descontar cantidad entregada (desde wizard)
                    # move_line.product_id.sudo().qty_on_hand_checked -= move_line.qty_check

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            return pickings_to_validate.with_context(skip_immediate=True).button_validate()
        return True


class WizardMessageMaxCamZeroCheck(models.TransientModel):
    _name = "wizard.message.verify.zero"
    _description = "Mensaje Confirmacion Zero"

    name_modal_message = fields.Char(string='Mensaje')
    picking_id = fields.Many2one('stock.picking', string='Orden')

    def button_confirm_zero(self):
        for record in self:
            record.picking_id.write({
                'verify_zero': True
            })
            record.picking_id.action_check_maxcam()
