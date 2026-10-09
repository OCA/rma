# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRmaBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.user
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.partner = cls.env["res.partner"].create({"name": "Customer A"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Customer B"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "consu", "is_storable": True}
        )
        cls.loc_stock = cls.env.ref("stock.stock_location_stock")
        cls.loc_customers = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.loc_stock, 100
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product2, cls.loc_stock, 100
        )
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.team = cls.env["rma.team"].create(
            {"name": "Team A", "user_id": cls.user.id}
        )
        cls.tag1 = cls.env["rma.tag"].create({"name": "Tag 1"})
        cls.tag2 = cls.env["rma.tag"].create({"name": "Tag 2"})
        cls.operation = cls.env.ref("rma_batch_return.rma_operation_receipt_and_refund")
        cls.warehouse.rma_in_type_id.create_rma_at_confirm = True
        cls.warehouse.rma_in_type_id.rma_create_operation_id = cls.operation

    def test_rma_return(self):
        self.batch = self.env["rma.batch"].search([])
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.warehouse.rma_in_type_id.id,
            }
        )
        destination = self.warehouse.rma_in_type_id.default_location_dest_id
        self.move_1 = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "name": self.product.name,
                "product_uom_qty": 2.0,
                "location_id": self.warehouse.rma_in_type_id.default_location_src_id.id,
                "location_dest_id": destination.id,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
            }
        )

        self.move_2 = self.env["stock.move"].create(
            {
                "product_id": self.product2.id,
                "name": self.product.name,
                "product_uom_qty": 2.0,
                "location_id": self.warehouse.rma_in_type_id.default_location_src_id.id,
                "location_dest_id": destination.id,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
            }
        )

        self.picking.action_confirm()
        self.picking.action_assign()

        self.picking.move_line_ids.picked = True
        self.picking._action_done()

        self.new_batch = self.env["rma.batch"].search([]) - self.batch

        self.assertTrue(self.new_batch)

        self.assertEqual(2, len(self.new_batch.rma_ids))

        self.assertEqual(1, self.new_batch.count_receipts)

        self.new_batch.action_confirm()

        self.assertTrue(self.new_batch.can_be_refunded)

    def test_rma_return_from_batch(self):
        # Create an RMA batch
        # Launch the action to create the receipt picking
        self.batch = self.env["rma.batch"].create(
            {
                "partner_id": self.partner.id,
                "operation_id": self.operation.id,
            }
        )

        self.assertFalse(self.batch.can_be_refunded)

        self.assertTrue(self.batch.new_receipt_button_visible)

        self.batch.action_create_blank_return_picking()

        self.assertTrue(self.batch.receipt_ids)

        self.assertFalse(self.batch.new_receipt_button_visible)

        self.picking = self.batch.receipt_ids
        destination = self.warehouse.rma_in_type_id.default_location_dest_id
        self.move_1 = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "name": self.product.name,
                "product_uom_qty": 2.0,
                "location_id": self.warehouse.rma_in_type_id.default_location_src_id.id,
                "location_dest_id": destination.id,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
            }
        )

        self.move_2 = self.env["stock.move"].create(
            {
                "product_id": self.product2.id,
                "name": self.product.name,
                "product_uom_qty": 2.0,
                "location_id": self.warehouse.rma_in_type_id.default_location_src_id.id,
                "location_dest_id": destination.id,
                "product_uom": self.product.uom_id.id,
                "picking_id": self.picking.id,
            }
        )

        self.picking.action_confirm()
        self.picking.action_assign()

        self.picking.move_line_ids.picked = True
        self.picking._action_done()

        self.assertEqual(2, len(self.batch.rma_ids))

        self.assertEqual(1, self.batch.count_receipts)

        self.batch.action_confirm()

        self.assertTrue(self.batch.can_be_refunded)

        result = self.batch.action_view_receipts()

        self.assertEqual(result.get("domain"), [("id", "in", self.picking.ids)])

        # Do the refund
        self.batch.action_refund()
        self.assertEqual(1, len(self.batch.rma_ids.partner_invoice_id))
