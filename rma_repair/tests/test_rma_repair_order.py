# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class RMARepairOrderTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse_company = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=1
        )
        cls.rma_loc = cls.warehouse_company.rma_loc_id
        cls.res_partner = cls.env["res.partner"].create({"name": "Test"})
        cls.rma = cls.env["rma"].create(
            {
                "product_id": cls.env.ref("product.product_delivery_01").id,
                "product_uom_qty": 2,
                "location_id": cls.rma_loc.id,
                "partner_id": cls.res_partner.id,
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

    def test_action_create_repair_order(self):
        action_result = self.rma.action_create_repair_order()
        self.assertEqual(
            action_result["context"],
            {
                "default_rma_ids": [self.rma.id],
                "default_product_id": self.rma.product_id.id,
                "default_location_id": self.rma.location_id.id,
                "default_partner_id": self.rma.partner_id.id,
            },
        )
        self.assertEqual(self.rma.repair_id, self.repair_order)
        self.assertEqual(self.rma.repair_id.product_id, self.repair_order.product_id)
        self.assertEqual(self.rma.repair_id.product_qty, self.repair_order.product_qty)
        self.assertEqual(self.rma.repair_id.location_id, self.repair_order.location_id)

    def test_rma_repair_order_done(self):
        self.rma.action_confirm()
        self.rma.reception_move_id.picking_id.button_validate()
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_end()
        self.assertTrue(self.rma.can_be_returned)
        self.assertFalse(self.rma.can_be_replaced)
        self.assertFalse(self.rma.can_be_refunded)

    def test_rma_repair_order_cancel(self):
        self.rma.action_confirm()
        self.rma.reception_move_id.picking_id.button_validate()
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_cancel()
        self.assertFalse(self.rma.can_be_returned)
        self.assertTrue(self.rma.can_be_replaced)
        self.assertTrue(self.rma.can_be_refunded)

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
                "name": "RMAs - " + self.repair_order.name,
                "type": "ir.actions.act_window",
                "view_mode": "tree,form",
                "res_model": "rma",
                "domain": [("id", "in", self.repair_order.rma_ids.ids)],
            },
        )
