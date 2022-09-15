# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestSaleOrderE(TransactionCase):
	print("----------------------TEST VENFOOD SALE EXTEND  ----------------------------------")

	def setUp(self):
		super(TestSaleOrderE, self).setUp()
		SaleOrder = self.env['sale.order'].with_context(tracking_disable=True)
		SaleOrderLine = self.env['sale.order.line'].with_context(tracking_disable=True)
		self.partner_1 = self.env['res.partner'].create({
			'id': 3,
			'name': 'Juan',
		})
		self.sale_order = SaleOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.sale_order_exempt = SaleOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.sale_order_taxed = SaleOrder.create({
			'partner_id': self.partner_1.id,
		})
		self.tax = self.env['account.tax'].create({
			'name': 'Tax 16.0',
			'amount': 16.0,
			'amount_type': 'percent',
			'type_tax_use': 'sale',
		})
		self.tax2 = self.env['account.tax'].create({
			'name': 'Tax 00.0',
			'amount': 00.0,
			'amount_type': 'percent',
			'type_tax_use': 'sale',
		})
		self.product = self.env['product.product'].create(
			{'name': 'producto'})
		self.sale_order_line_1 = SaleOrderLine.create({
			'order_id': self.sale_order.id,
			'name': "producto 1",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 1000,
			'price_total': 1000 * 1,
			'tax_id': [(6, 0, [self.tax.id])],
		})
		self.sale_order_line_2 = SaleOrderLine.create({
			'order_id': self.sale_order.id,
			'name': "producto 2",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 500,
			'price_total': 500*1,
			'tax_id': [(6, 0, [self.tax2.id])],
		})
		self.sale_order_line_3 = SaleOrderLine.create({
			'order_id': self.sale_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 300,
			'price_total': 300 * 1,
			'tax_id': [(6, 0, [self.tax2.id])],
		})
		self.sale_order_line_4 = SaleOrderLine.create({
			'order_id': self.sale_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'tax_id': [(6, 0, [self.tax2.id])],
		})
		self.sale_order_line_5 = SaleOrderLine.create({
			'order_id': self.sale_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'tax_id': [(6, 0, [self.tax2.id])],
		})
		self.sale_order_line_6 = SaleOrderLine.create({
			'order_id': self.sale_order_exempt.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'tax_id': [(6, 0, [self.tax.id])],
		})
		self.sale_order_line_7 = SaleOrderLine.create({
			'order_id': self.sale_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 300,
			'price_total': 300 * 1,
			'tax_id': [(6, 0, [self.tax.id])],
		})
		self.sale_order_line_8 = SaleOrderLine.create({
			'order_id': self.sale_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'tax_id': [(6, 0, [self.tax.id])],
		})
		self.sale_order_line_9 = SaleOrderLine.create({
			'order_id': self.sale_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 600,
			'price_total': 600 * 1,
			'tax_id': [(6, 0, [self.tax.id])],
		})
		self.sale_order_line_10 = SaleOrderLine.create({
			'order_id': self.sale_order_taxed.id,
			'name': "producto",
			'product_id': self.product.id,
			'product_uom_qty': 1,
			'price_unit': 100,
			'price_total': 100 * 1,
			'tax_id': [(6, 0, [self.tax2.id])],
		})

	def test_sum_exempt_taxed(self):
		self.assertEqual(self.sale_order.amount_exempt + self.sale_order.amount_taxed, 1500)

	def test_sum_exempt(self):
		self.assertEqual(self.sale_order_exempt.amount_exempt, 500)

	def test_sum_exempt(self):
		self.assertEqual(self.sale_order_taxed.amount_taxed, 1000)


