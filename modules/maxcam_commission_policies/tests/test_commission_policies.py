import logging
from random import randint

from dateutil.relativedelta import relativedelta
from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import tagged
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestCommissionPolicies(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ProductBrand = cls.env['product.brand']
        cls.CommissionPolicy = cls.env['commission.policy']
        cls.CommissionPolicyLine = cls.env['commission.policy.line']

        cls.brand_a = cls.ProductBrand.create({'name': 'Brand A', 'partner_id': cls.partner_a.id})
        cls.brand_b = cls.ProductBrand.create({'name': 'Brand B', 'partner_id': cls.partner_a.id})

        cls.product_a.write({'brand_id': cls.brand_a.id})
        cls.product_b.write({'brand_id': cls.brand_b.id})

        cls.vip_clients_commission_policy = cls.CommissionPolicy.create({
            "name": "Test Partner Policy",
            "policy_type": 'client',
            "clients_id": [
                (6, 0, [cls.partner_a.id, cls.partner_b.id])
            ],
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -90,
                        'date_until': 10,
                        'commission': 5
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 11,
                        'date_until': 20,
                        'commission': 4
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 21,
                        'date_until': 0,
                        'commission': 1
                    }
                )
            ]
        })
        cls.product_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Products Policy",
            "policy_type": 'product',
            "product_commission_type": "product",
            "products_id": (6, 0, [cls.product_a.id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -90,
                        'date_until': 8,
                        'commission': 8
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 9,
                        'date_until': 14,
                        'commission': 7
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 21,
                        'date_until': 0,
                        'commission': 3
                    }
                )
            ]
        })
        cls.product_brand_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Product Brand Policy",
            "policy_type": 'product',
            "product_commission_type": "brand",
            "products_id": (6, 0, [cls.brand_b.id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -70,
                        'date_until': 21,
                        'commission': 12
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 22,
                        'date_until': 30,
                        'commission': 10
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 31,
                        'date_until': 0,
                        'commission': 9
                    }
                )
            ]
        })
        cls.product_categories_commission_policies = cls.CommissionPolicy.create({
            "name": "Test Product Categories Policy",
            "policy_type": 'product',
            "product_commission_type": "category",
            "products_id": (6, 0, [cls.env.ref('product.product_category_all').id]),
            "commission_line_ids": [
                (
                    0,
                    0,
                    {
                        'date_from': -80,
                        'date_until': 15,
                        'commission': 50
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 16,
                        'date_until': 25,
                        'commission': 30
                    }
                ),
                (
                    0,
                    0,
                    {
                        'date_from': 26,
                        'date_until': 0,
                        'commission': 20
                    }
                )
            ]
        })

        cls.tax_group = cls.env["account.tax.group"].create({"name": "Tax"})

        cls.employee_bill = cls.env["hr.employee"].create({
            "name": "Bill Seller",
            "department_id": cls.env.ref("hr.dep_sales").id,
            "resource_calendar_id": cls.env.ref("resource.resource_calendar_std").id,
        })
        cls.delivery_method = cls.env["delivery.carrier"].create({
            "name": "Delivery Method",
            "delivery_type": "base_on_rule",
            "product_id": cls.company_data["product_service_delivery"].id,
            "margin": 0.0,
            "free_over": True,
            "amount": 0.0001,
            "fixed_price": 0.0,
        })

    def setup_invoice_based_in_out_picking(self, products: list):
        """ The function creates a invoice obj prepared to be used to calculate the commission cases """

        sale_order = self.env["sale.order"]
        out_invoice = self.env["account.move"]
        rand_qty = []

        with Form(self.env['sale.order']) as so_form:
            so_form.partner_id = self.partner_a
            for index, product in enumerate(products):
                rand_qty.append(randint(1, 10))
                with so_form.order_line.new() as line_form:
                    line_form.product_id = product
                    line_form.price_unit = 100
                    line_form.product_uom_qty = rand_qty[index]

            so_form.action_confirm()
            sale_order = so_form.save()

        out_picking_to_invoice = sale_order.picking_ids \
            .filtered(lambda p: p.picking_type_id == self.env.ref('stock.picking_type_out'))
        with Form(out_picking_to_invoice) as out_picking_form:
            for index, line in enumerate(out_picking_form.move_line_ids_without_package):
                with line.new() as line_form:
                    line_form.qty_done = rand_qty[index]
            out_picking_to_invoice.action_check_maxcam()
            out_picking_to_invoice.button_validate()
            out_invoice = out_picking_to_invoice \
                .action_invoice_create(journal_id=self.company_data.get('default_journal_sale').id)

        return out_invoice

    def test_commission_for_partners(self):
        """ Test that the commission is correctly settled for partners """

        with Form(self.vip_clients_commission_policy) as commission_policy_form:
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when partner is selected")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when partner is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when partner is selected")
            self.assertIs(commission_policy_form.product_commission_type, False,
                          "Product commission type should not be set when partner is selected")

            commission_policy_form.policy_type_id = self.policy_type_product.id
            commission_policy_form.product_commission_type = "product"
            self.assertIs(commission_policy_form.clients_id, False,
                          "Partners should not be set when product is selected")

    def test_commission_for_product_product(self):
        """ Test that the commission is correctly settled for products """

        with Form(self.product_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "product")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when product is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when product is selected")

    def test_commission_for_product_brand(self):
        """ Test that the commission is correctly settled for brands """

        with Form(self.product_brand_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "brand")
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when brand is selected")
            self.assertIs(commission_policy_form.categories_id, False,
                          "Categories should not be set when product is selected")

    def test_commission_for_product_category(self):
        """ Test that the commission is correctly settled for categories """

        with Form(self.product_brand_commission_policies) as commission_policy_form:
            self.assertIs(commission_policy_form.clients_id, False,
                          "Clients should not be set when product is selected")
            self.assertEqual(commission_policy_form.product_commission_type, "category")
            self.assertIs(commission_policy_form.products_id, False,
                          "Products should not be set when brand is selected")
            self.assertIs(commission_policy_form.brands_id, False, "Brands should not be set when product is selected")

    def test_commission_date_overlap_below(self):
        """ Test where the commission date last range overlap below the date_until
            of the previous range """

        with self.assertRaises(ValidationError):
            test_commission_1 = self.CommissionPolicy.create({
                "name": "Test Commission 1",
                "policy_type": 'all',
                "commission_line_ids": [
                    (
                        0,
                        0,
                        {
                            'date_from': -80,
                            'date_until': 15,
                            'commission': 5
                        }
                    ),
                    (
                        0,
                        0,
                        {
                            'date_from': 14,
                            'date_until': 26,
                            'commission': 4
                        }
                    )
                ]
            })

    def test_commission_date_overlap_equal(self):
        """ Test where the commission date last range overlap equally with the date_until
            of the previous range """

        with self.assertRaises(ValidationError):
            test_commission_2 = self.CommissionPolicy.create({
                "name": "Test Commission 2",
                "policy_type": 'all',
                "commission_line_ids": [
                    (
                        0,
                        0,
                        {
                            'date_from': -80,
                            'date_until': 15,
                            'commission': 5
                        }
                    ),
                    (
                        0,
                        0,
                        {
                            'date_from': 15,
                            'date_until': 26,
                            'commission': 4
                        }
                    )
                ]
            })

    def test_total_commission_calculation_of_product_priority_range_1(self):
        """ Test that the total commission is correctly calculated for the product
            in product-product ranges if best scenario """

        out_invoice = self.setup_invoice_based_in_out_picking(products=[self.product_a])
        self.assertCommissionPolicy(out_invoice, 2, 5, 'The range should fall into 5 as best case scenario')

    def test_total_commission_calculation_of_product_priority_range_2(self):
        """ Test that the total commission is correctly calculated for the product
            in product-product ranges if a second case scenario """

        out_invoice_2 = self.setup_invoice_based_in_out_picking(products=[self.product_a])
        self.assertCommissionPolicy(out_invoice_2, 10, 4, 'The range should fall into 4 as mid case scenario')

    def test_total_commission_calculation_of_product_priority_range_3(self):
        """ Test that the total commission is correctly calculated for the product
         in product-product ranges if is de the default las case scenario """

        out_invoice_3 = self.setup_invoice_based_in_out_picking(products=[self.product_a])
        self.assertCommissionPolicy(out_invoice_3, 23, 1, 'The range should fall into 1 as worst case scenario')

    def test_total_commission_calculation_for_multiple_cases(self):
        """ Test when an invoice have a vip partner, a product-product,
            a product-brand and a product-category commission """

        out_invoice_4 = self.setup_invoice_based_in_out_picking(products=[self.product_a, self.product_b, self.product])
        self.assertCommissionPolicy(out_invoice_4, 5, 8,
                                    'The range should fall into 75 as best multiple case scenario')

    def assertCommissionPolicy(self, invoice, date_step, commission_range, msg: str):
        """ Assert for every commission range that could be created for the given invoice """

        out_invoice = self.env["account.move"]

        self.assertRecordValues(invoice, [{
            'commission': 0,
            'reception_date_client': False,
            'last_payment_date': False
        }])

        with Form(invoice) as invoice_form:
            invoice_form.reception_date_client = Date.today()
            invoice_form.last_payment_date = Date.today() + relativedelta(days=date_step)
            out_invoice = invoice_form.save()

        self.assertEqual(out_invoice.commission, commission_range, msg)
