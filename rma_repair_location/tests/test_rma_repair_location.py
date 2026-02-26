# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.rma_repair.tests.test_rma_repair_order import RMARepairOrderTest


class TestRmaRepairLocation(RMARepairOrderTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wh = cls.env["stock.warehouse"].create(
            {"name": "Repair Warehouse", "code": "TESTWH"}
        )
        cls.loc = cls.env["stock.location"].create(
            {
                "name": "Repair Loc",
                "usage": "internal",
                "location_id": cls.wh.view_location_id.id,
            }
        )
        cls.operation.repair_warehouse_id = cls.wh
        cls.operation.repair_location_id = cls.loc

    def test_action_create_repair_order(self):
        action_result = self.rma.action_create_repair_order()
        ctx = action_result.get("context", {})
        self.assertEqual(ctx.get("default_warehouse_id"), self.wh.id)
        self.assertEqual(ctx.get("default_location_id"), self.loc.id)

    def test_create_repair_order(self):
        repair = self.rma_without_repair._create_repair()
        self.assertEqual(repair.warehouse_id, self.wh)
        self.assertEqual(repair.location_id, self.loc)
