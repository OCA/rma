# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from odoo.tests import common


class TestProductLotWarranty(common.TransactionCase):
    def test_productlot_warranty(self):
        company1 = self.env["res.company"].create({"name": "Test company1"})
        product1 = self.env["product.product"].create(
            {
                "name": "TestProduct",
                "warranty_type": "day",
                "warranty": 5,
            }
        )
        production_lot = self.env["stock.production.lot"].create(
            {"product_id": product1.id, "company_id": company1.id}
        )
        production_lot._onchange_product_id()
        self.assertEqual(
            production_lot.warranty_exp_date,
            (datetime.now() + timedelta(days=5)).date(),
        )
