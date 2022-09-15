# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderExemptTaxed(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_exempt = amount_taxed = 0.0
            for line in order.order_line:
                if line.product_id:
                    if line.tax_id and len(line.tax_id) == 1:
                        if line.tax_id.amount == 0:
                            amount_exempt += line.price_subtotal
                        else:
                            amount_taxed += line.price_subtotal
                    else:
                        pass
                    # raise UserError("Solo un impuesto por producto")
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
                'amount_exempt': amount_exempt,
                'amount_taxed': amount_taxed
            })

    amount_exempt = fields.Monetary(string='Exento', store=True, readonly=True, compute='_amount_all')
    amount_taxed = fields.Monetary(string='Gravado', store=True, readonly=True, compute='_amount_all')


class PurchaseOrderInhbin(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_exempt = amount_taxed = 0.0
            for line in order.order_line:
                if line.taxes_id:
                    # estaba line.tax_id.amount como en orden, pero ese un many2many y puede que tenga mas de un impuesto
                    if line.price_tax == 0:
                        amount_exempt += line.price_subtotal
                    else:
                        amount_taxed += line.price_subtotal
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
                'amount_exempt': amount_exempt,
                'amount_taxed': amount_taxed
            })

    amount_exempt = fields.Monetary(string='Exento', store=True, readonly=True, compute='_amount_all')
    amount_taxed = fields.Monetary(string='Gravado', store=True, readonly=True, compute='_amount_all')
