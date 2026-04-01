# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.rma_sale.tests.test_rma_sale import TestRmaSaleBase


@tagged("post_install", "-at_install")
class TestRmaSalePickingGroup(TestRmaSaleBase):
    """Test that RMA return pickings are visible from the SO."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rma_operation = cls.env["rma.operation"].create(
            {
                "name": "Test Return (picking group)",
                "action_create_receipt": "automatic_on_confirm",
                "action_create_delivery": "manual_after_receipt",
                "action_create_refund": False,
            }
        )

    @classmethod
    def _create_confirmed_and_delivered_sale(cls):
        order = cls._create_sale_order([(cls.product_1, 1)])
        order.action_confirm()
        for picking in order.picking_ids:
            picking.action_assign()
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.button_validate()
        return order

    def test_procurement_group_has_sale_ids(self):
        """RMA procurement group must have sale_ids (M2M) populated."""
        order = self._create_confirmed_and_delivered_sale()
        delivery_move = order.picking_ids.move_ids.filtered(
            lambda move: move.state == "done"
        )[:1]
        rma = self.env["rma"].create(
            {
                "partner_id": order.partner_id.id,
                "order_id": order.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "operation_id": self.rma_operation.id,
                "location_id": self.wh.rma_loc_id.id,
                "move_id": delivery_move.id,
                "picking_id": delivery_move.picking_id.id,
            }
        )
        rma.action_confirm()
        group = rma.procurement_group_id
        self.assertIn(
            order,
            group.sale_ids,
            "Procurement group must include the SO in sale_ids (M2M)",
        )

    def test_rma_return_picking_visible_from_sale_order(self):
        """RMA return picking must appear in sale.order.picking_ids."""
        order = self._create_confirmed_and_delivered_sale()
        delivery_move = order.picking_ids.move_ids.filtered(
            lambda move: move.state == "done"
        )[:1]
        rma = self.env["rma"].create(
            {
                "partner_id": order.partner_id.id,
                "order_id": order.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 1,
                "operation_id": self.rma_operation.id,
                "location_id": self.wh.rma_loc_id.id,
                "move_id": delivery_move.id,
                "picking_id": delivery_move.picking_id.id,
            }
        )
        rma.action_confirm()
        reception_picking = rma.reception_move_id.picking_id
        self.assertTrue(reception_picking)
        self.assertIn(
            reception_picking,
            order.picking_ids,
            "RMA return picking must be visible from the SO 'Deliveries' button",
        )
