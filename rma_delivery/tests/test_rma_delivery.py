# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaDelivery(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier_product = cls.product_product.create(
            {"name": "Delivery product test 1", "type": "service"}
        )
        cls.replace_product = cls.product_product.create(
            {"name": "Replace product test 1", "type": "product"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Fixed delivery method",
                "product_id": cls.carrier_product.id,
            }
        )
        cls.carrier_customer = cls.env["delivery.carrier"].create(
            {
                "name": "Test Customer delivery method",
                "product_id": cls.carrier_product.id,
            }
        )
        cls.partner.property_delivery_carrier_id = cls.carrier_customer
        cls.partner_shipping.property_delivery_carrier_id = False
        cls.company.rma_fixed_delivery_method = cls.carrier

    def _return_to_customer(self, rma, delivery_type="return"):
        """Helper to return the rma"""
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids, rma_delivery_type=delivery_type,
            )
        )
        if delivery_type == "replace":
            delivery_form.product_id = self.replace_product
        delivery_form.product_uom_qty = 1
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        return rma.delivery_move_ids.picking_id

    def test_01_fixed_method(self):
        """Fixed method. RMA gets the company default carrier"""
        # Return picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        self.company.rma_delivery_strategy = "fixed_method"
        picking = self._return_to_customer(rma)
        self.assertEqual(
            picking.carrier_id,
            self.carrier,
            "The carrier isn't the one set in the company as default",
        )
        # Replace picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma, "replace")
        self.assertEqual(
            picking.carrier_id,
            self.carrier,
            "The carrier isn't the one set in the company as default",
        )

    def test_02_customer_method(self):
        """Customer method. RMA gets the carrier from the contact"""
        # Return picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        self.company.rma_delivery_strategy = "customer_method"
        picking = self._return_to_customer(rma)
        self.assertEqual(
            picking.carrier_id,
            self.carrier_customer,
            "The carrier isn't the same one as in the commercial partner",
        )
        carrier_2 = self.env["delivery.carrier"].create(
            {"name": "Test delivery method", "product_id": self.carrier_product.id}
        )
        self.partner_shipping.property_delivery_carrier_id = carrier_2
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma)
        self.assertEqual(
            picking.carrier_id,
            carrier_2,
            "The carrier isn't the same one as in the picking partner",
        )
        # Replace picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma, "replace")
        self.assertEqual(
            picking.carrier_id,
            carrier_2,
            "The carrier isn't the same one as in the picking partner",
        )

    def test_03_mixed_method(self):
        """Mixed method. RMA gets the carrier from the contact otherwise the company
        default one"""
        # Return picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        self.company.rma_delivery_strategy = "mixed_method"
        picking = self._return_to_customer(rma)
        self.assertEqual(
            picking.carrier_id,
            self.carrier_customer,
            "The carrier isn't the same one as in the commercial partner",
        )
        self.partner.property_delivery_carrier_id = False
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma)
        self.assertEqual(
            picking.carrier_id,
            self.carrier,
            "The carrier isn't the one set in the company as default",
        )
        # Replace picking
        rma = self._create_confirm_receive(
            self.partner_shipping, self.product, 1, self.rma_loc
        )
        picking = self._return_to_customer(rma, "replace")
        self.assertEqual(
            picking.carrier_id,
            self.carrier,
            "The carrier isn't the one set in the company as default",
        )
