# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import Form

from .test_rma import TestRma


class TestRmaOperation(TestRma):
    def test_01(self):
        """
        ensure that the receipt creation behaves correctly according to the
        action_create_receipt setting.
        - "automatic_on_confirm":
            - receipts are created automatically
            - the manual button is hidden
        - "manual_on_confirm"
            - manual button is visible after confirmation
            - disappears once a receipt is manually created
        """
        self.assertEqual(self.operation.action_create_receipt, "automatic_on_confirm")
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.show_create_receipt)
        rma.action_confirm()
        self.assertTrue(rma.reception_move_id)
        self.assertFalse(rma.show_create_receipt)
        self.operation.action_create_receipt = "manual_on_confirm"
        rma2 = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma2.action_confirm()
        self.assertTrue(rma2.show_create_receipt)
        self.assertFalse(rma2.reception_move_id)
        rma2.action_create_receipt()
        self.assertFalse(rma2.show_create_receipt)

    def test_02(self):
        """
        test delivery button visibility based on operation settings.
        No deliver possible
        """
        self.operation.action_create_delivery = False
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.show_create_return)
        self.assertFalse(rma.can_be_replaced)
        self.assertFalse(rma.show_create_replace)

    def test_03(self):
        """
        test delivery button visibility based on operation settings.
        deliver manually after confirm
        """
        self.operation.action_create_delivery = "manual_on_confirm"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.show_create_return)
        self.assertTrue(rma.can_be_replaced)
        self.assertTrue(rma.show_create_replace)

    def test_04(self):
        """
        test delivery button visibility based on operation settings.
        deliver automatically after confirm, return same product
        """
        self.operation.action_create_delivery = "automatic_on_confirm"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.action_confirm()
        self.assertEqual(rma.state, "waiting_replacement")
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.show_create_return)
        self.assertFalse(rma.can_be_replaced)
        self.assertFalse(rma.show_create_replace)
        self.assertTrue(rma.delivery_move_ids)
        self.assertEqual(rma.delivery_move_ids.product_id, self.product)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 10)

    def test_05(self):
        """
        test delivery button visibility based on operation settings.
        deliver manually after receipt
        """
        self.operation.action_create_delivery = "manual_after_receipt"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.show_create_return)
        self.assertFalse(rma.can_be_replaced)
        self.assertFalse(rma.show_create_replace)
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.state, "received")
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.show_create_return)
        self.assertTrue(rma.can_be_replaced)
        self.assertTrue(rma.show_create_replace)

    def test_06(self):
        """
        test delivery button visibility based on operation settings.
        deliver automatically after receipt
        """
        self.operation.action_create_delivery = "automatic_after_receipt"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.show_create_return)
        self.assertFalse(rma.can_be_replaced)
        self.assertFalse(rma.show_create_replace)
        self.assertFalse(rma.delivery_move_ids)
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.delivery_move_ids.product_id, self.product)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 10)
        self.assertEqual(rma.state, "waiting_replacement")
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.show_create_return)
        self.assertTrue(rma.can_be_replaced)
        self.assertFalse(rma.show_create_replace)

    def test_07(self):
        """
        test delivery button visibility based on operation settings.
        deliver automatically after confirm, different product
        """
        self.operation.action_create_delivery = "automatic_on_confirm"
        self.operation.different_return_product = True
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        with self.assertRaises(AssertionError, msg="Replacement fields are required"):
            with Form(rma) as rma_form:
                rma_form.save()
        with self.assertRaises(
            ValidationError, msg="Complete the replacement information"
        ):
            rma.action_confirm()
        rma.return_product_id = self.product_product.create(
            {"name": "return Product test 1", "type": "product"}
        )
        rma.action_confirm()
        self.assertEqual(rma.delivery_move_ids.product_id, rma.product_id)
        self.assertEqual(rma.reception_move_id.product_id, rma.return_product_id)
        self.assertEqual(rma.state, "waiting_replacement")

    def test_08(self):
        """test refund, manually after confirm"""
        self.operation.action_create_refund = "manual_on_confirm"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.show_create_refund)

    def test_09(self):
        """test refund, manually after receipt"""
        self.operation.action_create_refund = "manual_after_receipt"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.show_create_refund)
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.state, "received")
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.show_create_refund)

    def test_10(self):
        """test refund, automatic after confirm"""
        self.operation.action_create_refund = "automatic_on_confirm"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "refunded")
        self.assertTrue(rma.refund_id)
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.show_create_refund)

    def test_11(self):
        """test refund, automatic after confirm"""
        self.operation.action_create_refund = "automatic_after_receipt"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "confirmed")
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.state, "refunded")
        self.assertTrue(rma.refund_id)
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.show_create_refund)

    def test_12(self):
        """
        Refund without product return
        Some companies may offer refunds without requiring the return of the product,
        often in cases of low-value items or when the cost of return shipping is
        prohibitive.
            - no receipt
            - no return
            - automatically refund on confirm
        """
        self.operation.action_create_receipt = False
        self.operation.action_create_refund = "automatic_on_confirm"
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "refunded")
        self.assertFalse(rma.reception_move_id)
        self.assertTrue(rma.refund_id)

    def test_13(self):
        """
        Return of non-ordered product
        Occasionally, customers receive items they did not order and need a process for
        returning these products. The delivered product don't figure on the sale order
        - receipt
        - no return
        - no refund
        """
        self.operation.action_create_receipt = "automatic_on_confirm"
        self.operation.action_create_delivery = False
        self.operation.action_create_refund = False
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id._action_done()
        self.assertEqual(rma.state, "received")
        self.assertFalse(rma.delivery_move_ids)

    def test_14(self):
        """if the refund action is not ment to update quantity, return picking line
        to_refund field should be False"""
        self.operation.action_create_refund = "manual_after_receipt"
        origin_delivery = self._create_delivery()
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=origin_delivery.ids,
                active_id=origin_delivery.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking_form.create_rma = True
        stock_return_picking_form.rma_operation_id = self.operation
        return_wizard = stock_return_picking_form.save()
        return_line = return_wizard.product_return_moves.filtered(
            lambda m, p=self.product: m.product_id == p
        )
        self.assertEqual(return_line.rma_operation_id, self.operation)
        picking_action = return_wizard.create_returns()
        reception = self.env["stock.picking"].browse(picking_action["res_id"])
        move = reception.move_ids.filtered(lambda m, p=self.product: m.product_id == p)
        self.assertFalse(move.to_refund)

    def test_15(self):
        """if the refund action is ment to update quantity, return picking line
        to_refund field should be True"""
        self.operation.action_create_refund = "update_quantity"
        origin_delivery = self._create_delivery()
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=origin_delivery.ids,
                active_id=origin_delivery.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking_form.create_rma = True
        stock_return_picking_form.rma_operation_id = self.operation
        return_wizard = stock_return_picking_form.save()
        return_line = return_wizard.product_return_moves.filtered(
            lambda m, p=self.product: m.product_id == p
        )
        self.assertEqual(return_line.rma_operation_id, self.operation)
        picking_action = return_wizard.create_returns()
        reception = self.env["stock.picking"].browse(picking_action["res_id"])
        move = reception.move_ids.filtered(lambda m, p=self.product: m.product_id == p)
        self.assertTrue(move.to_refund)

    def test_rma_replace_pick_ship(self):
        self.operation.action_create_delivery = "automatic_on_confirm"
        self.warehouse.write({"delivery_steps": "pick_ship"})
        rma = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.state, "waiting_replacement")
        out_pickings = rma.mapped("delivery_move_ids.picking_id")
        self.assertEqual(rma.delivery_picking_count, 2)
        self.assertIn(
            self.warehouse.pick_type_id, out_pickings.mapped("picking_type_id")
        )
        self.assertIn(
            self.warehouse.out_type_id, out_pickings.mapped("picking_type_id")
        )

    def test_16(self):
        rma = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.reception_move_id.state, "assigned")
        self.assertEqual(rma.reception_move_id.picking_id.state, "assigned")

    def test_17(self):
        self.operation.auto_confirm_reception = True
        rma = self._create_rma(self.partner, self.product, 1, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.reception_move_id.state, "done")
        self.assertEqual(rma.reception_move_id.picking_id.state, "done")
