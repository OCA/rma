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
            {"name": "Unittest P1", "type": "product"}
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
        self.picking.move_line_ids.qty_done = qty
        self.picking._action_done()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.so.order_line.qty_delivered, qty)

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
