# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.rma.tests.test_rma import TestRma


class RMARepairOrderTest(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_return.action_create_repair = "automatic_on_confirm"
        cls.operation = cls.operation_return
        cls.rma = cls._create_rma(
            cls.partner, cls.product, 2, cls.rma_loc, cls.operation_return
        )
        repair_form = Form(
            cls.env["repair.order"].with_context(
                default_product_id=cls.rma.product_id.id,
                default_rma_ids=[cls.rma.id],
                default_product_location_src_id=cls.rma.location_id.id,
            )
        )
        cls.repair_order = repair_form.save()
        cls.rma_without_repair = cls._create_rma(
            cls.partner, cls.product, 2, cls.rma_loc, cls.operation_return
        )

    @classmethod
    def _receive_rma(cls, rma):
        rma.reception_move_id.picking_id.button_validate()

    def test_action_create_repair_order(self):
        action_result = self.rma.action_create_repair_order()
        ctx = action_result.get("context", {})
        expected = {
            "default_rma_ids": [self.rma.id],
            "default_product_id": self.rma.product_id.id,
            "default_product_location_src_id": self.rma.location_id.id,
            "default_partner_id": self.rma.partner_id.id,
            "default_product_qty": self.rma.product_uom_qty,
            "default_product_uom": self.rma.product_uom.id,
            "default_address_id": self.rma.partner_shipping_id.id,
            "default_partner_invoice_id": self.rma.partner_invoice_id.id,
            "default_picking_id": self.rma.reception_move_id.picking_id.id,
        }
        for key, expected_value in expected.items():
            self.assertIn(key, ctx, f"Missing context key: {key}")
            self.assertEqual(ctx[key], expected_value, f"Wrong value for {key}")

        self.assertEqual(self.rma.repair_id, self.repair_order)
        self.assertEqual(self.rma.repair_id.product_id, self.repair_order.product_id)
        self.assertEqual(self.rma.repair_id.product_qty, self.repair_order.product_qty)
        self.assertEqual(self.rma.repair_id.location_id, self.repair_order.location_id)

    def test_rma_repair_order_done(self):
        self.rma.action_confirm()
        self._receive_rma(self.rma)
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_end()
        self.assertTrue(self.rma.can_be_returned)
        self.assertFalse(self.rma.can_be_replaced)
        self.assertFalse(self.rma.can_be_refunded)

    def test_rma_repair_order_cancel(self):
        self.rma.action_confirm()
        self._receive_rma(self.rma)
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_cancel()
        self.assertFalse(self.rma.can_be_returned)
        self.assertTrue(self.rma.can_be_replaced)
        self.assertFalse(self.rma.can_be_refunded)

    def test_action_view_rma_repair_order(self):
        self.assertEqual(
            self.rma.action_view_rma_repair_order(),
            {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "repair.order",
                "res_id": self.repair_order.id,
            },
        )

    def test_action_view_repair_rma(self):
        self.assertEqual(
            self.repair_order.action_view_repair_rma(),
            {
                "name": f"RMAs - {self.repair_order.name}",
                "type": "ir.actions.act_window",
                "view_mode": "list,form",
                "res_model": "rma",
                "domain": [("id", "in", self.repair_order.rma_ids.ids)],
            },
        )

    def test_manually_create_repair_after_confirm(self):
        """
        ensure repair can't be created after confirm unless operation allows it

        - by default ("manual_after_receipt"), repair is not allowed after confirm
        - when set to "manual_on_confirm", repair becomes allowed
        - verify repair is created and no longer allowed afterward
        """

        self.operation.action_create_repair = False
        self.assertFalse(self.operation.action_create_repair)
        self.rma_without_repair.action_confirm()
        self.assertFalse(self.rma_without_repair.can_be_repaired)
        self.operation.action_create_repair = "manual_on_confirm"
        self.assertTrue(self.rma_without_repair.can_be_repaired)
        self.rma_without_repair._create_repair()
        self.assertTrue(self.rma_without_repair.repair_id)
        self.assertFalse(self.rma_without_repair.can_be_repaired)

    def test_automatically_create_repair_on_confirm(self):
        """
        test that repair is automatically created on confirm if operation allows it

        - with "automatic_on_confirm", repair is created during confirmation
        - verify repair is not manually allowed after confirm
        """
        self.operation.action_create_repair = "automatic_on_confirm"
        self.rma_without_repair.action_confirm()
        self.assertFalse(self.rma_without_repair.can_be_repaired)
        self.assertTrue(self.rma_without_repair.repair_id)

    def test_manually_create_repair_after_receipt(self):
        """
        test manual repair creation after receipt if operation allows it

        - with "manual_after_receipt", repair isn't allowed after confirm
        - after receipt, repair becomes allowed
        - verify repair is created and no longer allowed afterward
        """

        self.operation.action_create_repair = "manual_after_receipt"
        self.rma_without_repair.action_confirm()
        self.assertFalse(self.rma_without_repair.can_be_repaired)
        self._receive_rma(self.rma_without_repair)
        self.assertEqual(self.rma_without_repair.state, "received")
        self.assertTrue(self.rma_without_repair.can_be_repaired)
        self.rma_without_repair._create_repair()
        self.assertTrue(self.rma_without_repair.repair_id)
        self.assertFalse(self.rma_without_repair.can_be_repaired)

    def test_automatically_create_repair_after_receipt(self):
        """
        Test automatic repair creation after receipt

        - with "automatic_after_receipt", repair isn't allowed after confirm
        - repair is auto-created on receipt
        - verify repair is created and no longer allowed afterward
        """

        self.operation.action_create_repair = "automatic_after_receipt"
        self.rma_without_repair.action_confirm()
        self.assertFalse(self.rma_without_repair.can_be_repaired)
        self._receive_rma(self.rma_without_repair)
        self.assertEqual(self.rma_without_repair.state, "received")
        self.assertFalse(self.rma_without_repair.can_be_repaired)
        self.assertTrue(self.rma_without_repair.repair_id)
        self.assertFalse(self.rma_without_repair.can_be_repaired)
