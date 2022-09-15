# -*- coding: utf-8 -*-

# Copyright 2019 Manuel Calero Solís
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
#
# docker-compose run web --test-enable --stop-after-init -d test_db -i pos_combinated_drinks
#

from odoo.tests import common, datetime
from odoo.tests import Form, TransactionCase

import logging


class TestPosCombinatedDrinks(TransactionCase):

    def setUp(self):
        super(TestPosCombinatedDrinks, self).setUp()
        self.product_gin = self.env['res.partner'].create({
            'name': 'Gin',
            'customer': 'product',
            'supplier': 'gin',
        })

    def test_product_combinable_created(self):
      self.assertTrue(self.product_gin.is_combo)