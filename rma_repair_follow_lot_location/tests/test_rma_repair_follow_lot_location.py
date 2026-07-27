# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestRmaRepairFollowLotLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse_company = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=1
        )
        cls.rma_loc = cls.warehouse_company.rma_loc_id
        cls.res_partner = cls.env["res.partner"].create({"name": "Test"})
        cls.operation = cls.env.ref("rma.rma_operation_return")
        cls.action_create_repair = "manual_after_receipt"
        cls.rma = cls.env["rma"].create(
            {
                "product_id": cls.env.ref("product.product_delivery_01").id,
                "product_uom_qty": 2,
                "location_id": cls.rma_loc.id,
                "partner_id": cls.res_partner.id,
                "operation_id": cls.operation.id,
            }
        )
        repair_form = Form(
            cls.env["repair.order"].with_context(
                default_product_id=cls.rma.product_id.id,
                default_rma_ids=[cls.rma.id],
                default_location_id=cls.rma.location_id.id,
            )
        )
        cls.repair_order = repair_form.save()
        cls.rma_without_repair = cls.env["rma"].create(
            {
                "product_id": cls.env.ref("product.product_delivery_01").id,
                "product_uom_qty": 2,
                "location_id": cls.rma_loc.id,
                "partner_id": cls.res_partner.id,
                "operation_id": cls.operation.id,
            }
        )

    def test_action_create_repair_order_follow_lot_location(self):
        self.operation.repair_follow_lot_location = True
        action_result = self.rma.action_create_repair_order()
        ctx = action_result.get("context", {})
        key = "default_follow_lot_location"
        self.assertIn(key, ctx)
        self.assertTrue(ctx[key])

    def test_action_create_repair_order_no_follow_lot_location(self):
        self.operation.repair_follow_lot_location = False
        action_result = self.rma.action_create_repair_order()
        ctx = action_result.get("context", {})
        key = "default_follow_lot_location"
        self.assertIn(key, ctx)
        self.assertFalse(ctx[key])

    def test_create_repair_order_repair_follow_lot_location(self):
        self.operation.repair_follow_lot_location = True
        repair = self.rma_without_repair._create_repair()
        self.assertTrue(repair.follow_lot_location)

    def test_create_repair_order_repair_no_follow_lot_location(self):
        self.operation.repair_follow_lot_location = False
        repair = self.rma_without_repair._create_repair()
        self.assertFalse(repair.follow_lot_location)
