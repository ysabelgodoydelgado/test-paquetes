# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
class TestPurchaseInh(TransactionCase):
	print("----------------------TEST VENFOOD purchase EXTEND  ----------------------------------")

	def setUp(self):
		super(TestPurchaseInh, self).setUp()
		purchaseOrder = self.env['purchase.order'].with_context(tracking_disable=True)
		purchaseOrderLine = self.env['purchase.order.line'].with_context(tracking_disable=True)
		self.partner_1 = self.env['res.partner'].create({
			'id': 3,
			'name': 'Juan',
		})
		self.purchase_order = purchaseOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.purchase_order_exempt = purchaseOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.purchase_order_taxed = purchaseOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.tax = self.env['account.tax'].create({
			'name': 'Tax 16.0',
			'amount': 16.0,
			'amount_type': 'percent',
			'type_tax_use': 'purchase',
		})
		self.tax2 = self.env['account.tax'].create({
			'name': 'Tax 00.0',
			'amount': 00.0,
			'amount_type': 'percent',
			'type_tax_use': 'purchase',
		})
		self.product = self.env['product.product'].create(
			{'name': 'producto'})
		self.purchase_order_line_1 = purchaseOrderLine.create({
			'order_id': self.purchase_order.id,
			'name': "producto 1",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 1000,
			'price_total': 1000 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_2 = purchaseOrderLine.create({
			'order_id': self.purchase_order.id,
			'name': "producto 2",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 500,
			'price_total': 500*1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax2.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_3 = purchaseOrderLine.create({
			'order_id': self.purchase_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 300,
			'price_total': 300 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax2.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_4 = purchaseOrderLine.create({
			'order_id': self.purchase_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax2.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_5 = purchaseOrderLine.create({
			'order_id': self.purchase_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax2.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_6 = purchaseOrderLine.create({
			'order_id': self.purchase_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_7 = purchaseOrderLine.create({
			'order_id': self.purchase_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 300,
			'price_total': 300 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_8 = purchaseOrderLine.create({
			'order_id': self.purchase_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'product_uom': self.product.uom_po_id.id,
		})
		self.purchase_order_line_9 = purchaseOrderLine.create({
			'order_id': self.purchase_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom': self.product.uom_po_id.id,
			'product_uom_qty': 1,
			'price_unit': 600,
			'price_total': 600 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax.id])],
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
		})
		self.purchase_order_line_10 = purchaseOrderLine.create({
			'order_id': self.purchase_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'product_qty':1,
			'taxes_id': [(6, 0, [self.tax2.id])],
			'product_uom': self.product.uom_po_id.id,
			'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
		})

	def test_sum_exempt_taxed(self):
		self.assertEqual(self.purchase_order.amount_exempt + self.purchase_order.amount_taxed, 1500)

	def test_sum_exempt(self):
		self.assertEqual(self.purchase_order_exempt.amount_exempt, 500)

	def test_sum_exempt(self):
		self.assertEqual(self.purchase_order_taxed.amount_taxed, 1000)

	def test_purchase_order_amount(self):
		self.assertEqual(self.purchase_order.amount_exempt + self.purchase_order.amount_taxed, self.purchase_order.amount_untaxed)