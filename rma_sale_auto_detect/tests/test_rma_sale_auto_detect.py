# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import ValidationError

from .common import TestRmaSaleAutoDetectBase


class TestRmaSaleAutoDetect(TestRmaSaleAutoDetectBase):
    def test_0(self):
        """sale order older than the operation return eligibility period should not be
        linked automatically
        if a sale order is suggested by the user the link is created even if the
        eligibility period is not respected"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 60
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertTrue(rma.has_sale_auto_detect_issue)
        self.assertEqual(
            rma.sale_auto_detect_note,
            "No delivery move found or insufficient delivered quantity.",
        )
        rma.order_id = sale_order
        rma.action_link_rma_to_sale_line()
        self.assertTrue(rma.move_id)
        self.assertFalse(rma.has_sale_auto_detect_issue)
        self.assertFalse(rma.sale_auto_detect_note)

    def test_1(self):
        """exact match between rma and sale line delivered qty with one delivery"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertEqual(rma.move_id, sale_order.order_line.move_ids)
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma.order_id, sale_order)

    def test_2(self):
        """exact match between rma and sale line delivered qty with multiple
        deliveries"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 3)
        self._process_picking(sale_order.picking_ids, self.product, 2)
        self.assertEqual(len(sale_order.order_line.move_ids), 2)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertTrue(rma.move_id)
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma.order_id, sale_order)
        self.assertEqual(len(sale_order.rma_ids), 2)
        self.assertEqual(sum(sale_order.rma_ids.mapped("product_uom_qty")), 5)

    def test_3(self):
        """rma qty greater than sale line delivered qty with one delivery"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 10, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertEqual(rma.product_uom_qty, 5)
        new_rma = sale_order.rma_ids  # a new rma was created with the matched qty
        self.assertEqual(new_rma.sale_line_id, sale_order.order_line)
        self.assertEqual(new_rma.order_id, sale_order)
        self.assertEqual(new_rma.product_uom_qty, 5)
        self.assertTrue(rma.has_sale_auto_detect_issue)
        self.assertEqual(
            rma.sale_auto_detect_note,
            "No delivery move found or insufficient delivered quantity.",
        )

    def test_4(self):
        """rma qty greater than sale line delivered qty with multiple deliveries"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 10, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertEqual(rma.product_uom_qty, 5)
        new_rma = sale_order.rma_ids  # a new rma was created with the matched qty
        self.assertEqual(new_rma.sale_line_id, sale_order.order_line)
        self.assertEqual(new_rma.order_id, sale_order)
        self.assertEqual(new_rma.product_uom_qty, 5)

    def test_5(self):
        """rma qty smaller than sale line delivered qty with one delivery"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 10)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 10)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertEqual(rma.product_uom_qty, 5)
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma.order_id, sale_order)
        self.assertEqual(rma.product_uom_qty, 5)

    def test_6(self):
        """rma qty smaller than sale line delivered qty with multiple deliveries"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 10)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 3)
        self._process_picking(sale_order.picking_ids, self.product, 2)
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        matched_rmas = sale_order.rma_ids
        self.assertEqual(len(matched_rmas), 2)
        self.assertEqual(sum(matched_rmas.mapped("product_uom_qty")), 5)
        self.assertEqual(matched_rmas.sale_line_id, sale_order.order_line)
        self.assertEqual(matched_rmas.order_id, sale_order)

    def test_7(self):
        """rma linked to sale orders with different partners"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        sale_order2 = self._create_and_confirm_sale_order(
            self.partner2, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        self._process_picking(sale_order2.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma2 = self._create_rma(self.partner2, self.product, 5, self.operation)
        (rma + rma2).action_link_rma_to_sale_line()
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma.order_id, sale_order)
        self.assertEqual(rma2.sale_line_id, sale_order2.order_line)
        self.assertEqual(rma2.order_id, sale_order2)

    def test_8(self):
        """rma linked to sale orders with different partners and products"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5), (self.product2, 6)], 30
        )
        sale_order2 = self._create_and_confirm_sale_order(
            self.partner2, [(self.product, 5), (self.product2, 6)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        self._process_picking(sale_order.picking_ids, self.product2, 5)
        self._process_picking(sale_order2.picking_ids, self.product, 5)
        self._process_picking(sale_order2.picking_ids, self.product2, 6)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma2 = self._create_rma(self.partner2, self.product, 5, self.operation)
        rma3 = self._create_rma(self.partner2, self.product2, 5, self.operation)
        (rma + rma2 + rma3).action_link_rma_to_sale_line()

        self.assertEqual(
            rma.sale_line_id,
            sale_order.order_line.filtered(lambda sol: sol.product_id == self.product),
        )
        self.assertEqual(rma.order_id, sale_order)
        self.assertEqual(
            rma2.sale_line_id,
            sale_order2.order_line.filtered(lambda sol: sol.product_id == self.product),
        )
        self.assertEqual(rma2.order_id, sale_order2)
        self.assertEqual(
            rma3.sale_line_id,
            sale_order2.order_line.filtered(
                lambda sol: sol.product_id == self.product2
            ),
        )
        self.assertEqual(rma2.order_id, sale_order2)

    def test_9(self):
        """multiple rmas linked to the same sale line"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 10)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 10)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma2 = self._create_rma(self.partner, self.product, 3, self.operation)
        rma3 = self._create_rma(self.partner, self.product, 2, self.operation)
        (rma + rma2 + rma3).action_link_rma_to_sale_line()
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma2.sale_line_id, sale_order.order_line)
        self.assertEqual(rma3.sale_line_id, sale_order.order_line)
        rma4 = self._create_rma(self.partner, self.product, 2, self.operation)
        rma4.action_link_rma_to_sale_line()
        # all delivered qty already linked, new rma should not be linked
        self.assertFalse(rma4.sale_line_id)

    def test_10(self):
        """When user suggest the sale order and there is multiple delivery moves
        the rma is split"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 60
        )
        self._process_picking(sale_order.picking_ids, self.product, 3)
        self._process_picking(sale_order.picking_ids, self.product, 2)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        self.assertFalse(rma.return_eligibility_period_exceeded)
        rma.order_id = sale_order
        self.assertTrue(rma.return_eligibility_period_exceeded)
        rma.action_link_rma_to_sale_line()
        self.assertTrue(rma.move_id)
        self.assertFalse(rma.has_sale_auto_detect_issue)
        self.assertFalse(rma.sale_auto_detect_note)
        rmas = sale_order.order_line.move_ids.rma_ids
        self.assertEqual(len(rmas), 2)
        self.assertEqual(sum(rmas.mapped("product_uom_qty")), 5)

    def test_11(self):
        """sale order older than the operation return eligibility period should not be
        linked automatically, the ignore_sale_auto_detect should ignore the linking
        issue"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 60
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertTrue(rma.has_sale_auto_detect_issue)
        self.assertEqual(
            rma.sale_auto_detect_note,
            "No delivery move found or insufficient delivered quantity.",
        )
        rma.ignore_sale_auto_detect = True
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertFalse(rma.has_sale_auto_detect_issue)
        self.assertFalse(rma.sale_auto_detect_note)

    def test_12(self):
        """
        partial return:
        test that RMAs are linked to the sale line until the delivered quantity is
        fully consumed, and that any additional RMA is left unlinked
        """
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 10)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 10)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma2 = self._create_rma(self.partner, self.product, 3, self.operation)
        (rma + rma2).action_link_rma_to_sale_line()
        self.assertEqual(rma.sale_line_id, sale_order.order_line)
        self.assertEqual(rma2.sale_line_id, sale_order.order_line)
        rma3 = self._create_rma(self.partner, self.product, 2, self.operation)
        rma3.action_link_rma_to_sale_line()
        self.assertEqual(rma3.sale_line_id, sale_order.order_line)
        rma4 = self._create_rma(self.partner, self.product, 2, self.operation)
        rma4.action_link_rma_to_sale_line()
        # all delivered qty already linked, new rma should not be linked
        self.assertFalse(rma4.sale_line_id)
        (rma + rma2 + rma3).action_confirm()
        self.assertEqual(rma.state, "confirmed")
        # force th move
        rma4.write({"move_id": sale_order.order_line.move_ids.id})
        with self.assertRaisesRegex(
            ValidationError,
            "The quantity to return exceeds the remaining returnable "
            "quantity for this delivery",
        ):
            rma4.action_confirm()

    def test_13(self):
        """has_sale_auto_detect_issue is reset after rma set to draft"""
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 60
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        rma.action_link_rma_to_sale_line()
        self.assertFalse(rma.move_id)
        self.assertTrue(rma.has_sale_auto_detect_issue)
        self.assertEqual(
            rma.sale_auto_detect_note,
            "No delivery move found or insufficient delivered quantity.",
        )
        rma.action_cancel()
        self.assertEqual(rma.state, "cancelled")
        self.assertTrue(rma.has_sale_auto_detect_issue)
        self.assertTrue(rma.sale_auto_detect_note)
        rma.action_draft()
        self.assertEqual(rma.state, "draft")
        self.assertFalse(rma.has_sale_auto_detect_issue)
        self.assertFalse(rma.sale_auto_detect_note)

    def test_sale_order_reversed(self):
        """
        Create several sale orders
        Set the RMA operation to retrieve more recent sale orders first

        """
        self.operation.return_eligibility_order = "recent_first"
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5), (self.product2, 6)], 30
        )
        sale_order2 = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5), (self.product2, 6)], 28
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        self._process_picking(sale_order.picking_ids, self.product2, 5)
        self._process_picking(sale_order2.picking_ids, self.product, 5)
        self._process_picking(sale_order2.picking_ids, self.product2, 6)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)

        rma.action_link_rma_to_sale_line()

        self.assertEqual(
            rma.sale_line_id,
            sale_order2.order_line.filtered(lambda sol: sol.product_id == self.product),
        )
