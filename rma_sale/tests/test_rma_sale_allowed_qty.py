# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRmaSaleQuantityAllowed(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.loc_stock = cls.warehouse.lot_stock_id
        cls.partner1 = cls.env["res.partner"].create({"name": "Partner"})
        cls.p1 = cls.env["product.product"].create(
            {"name": "Unittest P1", "type": "consu", "is_storable": True}
        )
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner1.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.p1.name,
                            "product_id": cls.p1.id,
                            "product_uom_qty": 5,
                            "price_unit": 50,
                        },
                    )
                ],
            }
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.p1.id,
                "inventory_quantity": 10,
                "location_id": cls.loc_stock.id,
            }
        )._apply_inventory()
        cls.so.action_confirm()
        cls.picking = cls.so.picking_ids[0]

    def _get_rma_wizard(self):
        action = self.so.action_create_rma()
        return self.env[action.get("res_model")].browse(action.get("res_id"))

    def _deliver(self, qty):
        self.picking.move_ids.quantity = qty
        self.picking.move_ids.picked = True
        self.picking._action_done()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.so.order_line.qty_delivered, qty)

    def _create_rma_route_in_2_steps(self):
        """
        2 steps return route: Customer -> RMA Entrance -> RMA QC OK.
        """
        rma_entrance = self.env["stock.location"].create(
            {
                "name": "RMA: entrance before quality check",
                "usage": "internal",
            }
        )
        rma_reception = self.env["stock.picking.type"].create(
            {
                "name": "RMA Receptions",
                "code": "incoming",
                "sequence_code": "RMA-IN-REC",
                "default_location_src_id": self.env.ref(
                    "stock.stock_location_customers"
                ).id,
                "default_location_dest_id": rma_entrance.id,
            }
        )
        rma_qc = self.env["stock.picking.type"].create(
            {
                "name": "RMA QC",
                "code": "internal",
                "sequence_code": "RMA-QC",
                "default_location_src_id": rma_entrance.id,
                "default_location_dest_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,
            }
        )
        self.env["stock.route"].create(
            {
                "name": "RMA: In in 2 steps",
                "warehouse_selectable": "True",
                "warehouse_ids": [Command.link(self.warehouse.id)],
                "rule_ids": [
                    Command.create(
                        {
                            "name": "RMA Reception",
                            "action": "pull",
                            "picking_type_id": rma_reception.id,
                            "procure_method": "make_to_stock",
                            "location_src_id": rma_reception.default_location_src_id.id,
                            "location_dest_id": rma_entrance.id,
                        },
                    ),
                    Command.create(
                        {
                            "name": "RMA QC",
                            "action": "push",
                            "picking_type_id": rma_qc.id,
                            "auto": "manual",
                            "location_src_id": rma_entrance.id,
                            "location_dest_id": rma_qc.default_location_dest_id.id,
                        },
                    ),
                ],
            }
        )
        self.warehouse.rma_loc_id = rma_entrance

    def test_1(self):
        """
        Test rma wizard:

            - fully deliver the so
            - open rma wizard
        expected:
            - qty proposed: 5
            - allowed qty 5
            - qty 0 if is_return_all = False
        """
        self._deliver(5)
        wizard = self._get_rma_wizard()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.quantity, 5)
        self.assertEqual(wizard.line_ids.allowed_quantity, 5)
        wizard.is_return_all = False
        self.assertEqual(wizard.line_ids.quantity, 0)
        wizard.is_return_all = True
        self.assertEqual(wizard.line_ids.quantity, 5)

    def test_2(self):
        """
        Test rma wizard:

            - partially deliver the so
            - open rma wizard
        expected:
            - qty proposed: 3
            - allowed qty 3
            - qty 0 if is_return_all = False
        """
        self._deliver(3)
        wizard = self._get_rma_wizard()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.quantity, 3)
        self.assertEqual(wizard.line_ids.allowed_quantity, 3)
        wizard.is_return_all = False
        self.assertEqual(wizard.line_ids.quantity, 0)
        wizard.is_return_all = True
        self.assertEqual(wizard.line_ids.quantity, 3)

    def test_3(self):
        """
        Test rma wizard:
            Try to return more than the allowed qty
        """
        self._deliver(3)
        wizard = self._get_rma_wizard()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.quantity, 3)
        self.assertEqual(wizard.line_ids.allowed_quantity, 3)
        with self.assertRaises(
            ValidationError, msg="You can't exceed the allowed quantity"
        ):
            wizard.line_ids.quantity = 5
        wizard.line_ids.quantity = 1

    def test_4(self):
        """
        Test rma wizard:

            - deliver the so
            - return 1 unit with a return route generating 2 moves
            - open rma wizard
        expected:
            - qty proposed: 4
            - allowed qty 4
            - qty 0 if is_return_all = False
        """
        self._create_rma_route_in_2_steps()
        self._deliver(5)
        wizard = self._get_rma_wizard()
        wizard.line_ids[0].quantity = 1
        wizard.operation_id = self.env.ref("rma.rma_operation_refund").id
        rma = wizard.create_rma()
        rma.action_confirm()
        rma.reception_move_id.picking_id.button_validate()
        self.assertTrue(
            rma.reception_move_id.move_dest_ids,
            "Second step move for return should have been created",
        )
        rma.reception_move_id.move_dest_ids.picking_id.button_validate()
        # Returned product was received, QC ok. Both steps performed
        wizard = self._get_rma_wizard()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.quantity, 4)
        self.assertEqual(wizard.line_ids.allowed_quantity, 4)
