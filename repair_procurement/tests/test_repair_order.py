# Copyright 2021 Jarsa
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.tests.common import TransactionCase


class TestRepairOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.repair = self.env.ref("repair.repair_r1")
        self.stock_loc = self.env.ref("stock.stock_location_stock")
        self.spare_loc = self.env["stock.location"].create(
            {
                "name": "Spares",
                "usage": "internal",
            }
        )
        self.internal_type = self.env.ref("stock.picking_type_internal")
        self.spare_product = self.env.ref("product.product_product_11")
        self.route = self.env["stock.location.route"].create(
            {
                "name": "Stock -> Spares",
                "product_selectable": True,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Stock -> Spares",
                            "action": "pull",
                            "picking_type_id": self.internal_type.id,
                            "location_src_id": self.stock_loc.id,
                            "location_id": self.spare_loc.id,
                            "procure_method": "make_to_stock",
                            "group_propagation_option": "propagate",
                        },
                    )
                ],
            }
        )
        self.spare_product.write({"route_ids": [(4, self.route.id)]})

    def test_repair_order(self):
        self.repair.operations.write(
            {
                "location_id": self.spare_loc.id,
            }
        )
        self.repair.action_repair_confirm()
        self.assertEqual(len(self.repair.picking_ids), 1)
        self.repair.action_repair_cancel()
        self.assertEqual(self.repair.picking_ids.state, "cancel")
