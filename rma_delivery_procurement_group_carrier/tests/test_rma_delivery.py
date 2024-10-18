# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.rma_delivery.tests.test_rma_delivery import TestRmaDeliveryBase


class TestRmaDelivery(TestRmaDeliveryBase):
    def test_01_fixed_method(self):
        """Fixed method. RMA gets the company default carrier"""
        self.company.rma_delivery_strategy = "fixed_method"
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma)
        self.assertEqual(picking.carrier_id, self.carrier)
        self.assertEqual(rma.procurement_group_id.carrier_id, self.carrier)

    def test_02_customer_method(self):
        """Customer method. RMA gets the carrier from the contact"""
        self.company.rma_delivery_strategy = "customer_method"
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma)
        self.assertEqual(picking.carrier_id, self.carrier_customer)
        self.assertEqual(rma.procurement_group_id.carrier_id, self.carrier_customer)
