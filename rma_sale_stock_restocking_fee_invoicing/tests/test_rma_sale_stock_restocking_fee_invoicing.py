# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestRmaSaleStockRestockingFeeInvoicingCommon


class TestRmaSaleStockRestockingFeeInvoicing(
    TestRmaSaleStockRestockingFeeInvoicingCommon
):
    def test_0(self):
        """ensure restocking_fee_type enforces correct constraints on amount and
        percentage"""
        with self.assertRaisesRegex(
            ValidationError, "Restocking fee amount must be greater than zero"
        ):
            self.operation.restocking_fee_type = "fixed"
        with self.assertRaisesRegex(
            ValidationError, "Restocking fee amount must be greater than zero"
        ):
            self.operation.restocking_fee_type = "percent"

        with self.assertRaisesRegex(
            ValidationError, "Restocking fee percentage cannot exceed 100%"
        ):
            self.operation.write(
                {"restocking_fee_type": "percent", "restocking_fee_amount": 105}
            )

    def test_1(self):
        """no restocking fee is applied when restocking_fee_type is not set"""
        self.assertFalse(self.operation.restocking_fee_type)
        wizard = self._rma_sale_wizard(self.sale_order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertTrue(rma.reception_move_id)
        self.assertFalse(rma.reception_move_id.charge_restocking_fee)
        self.assertFalse(rma.manual_restocking_fee_invoice_needed)

    def test_2(self):
        """a restocking fee must not be added to the sale order when refund strategy
        is not 'update_quantity'"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "fixed", "restocking_fee_amount": 5.5}
        )
        self._create_receive_rma()
        self.assertEqual(len(self.sale_order.order_line), 1)

    def test_3(self):
        """when refund strategy is 'update_quantity' and fee type is fixed,
        a restocking fee line is added with the correct amount, fixed case"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "fixed", "restocking_fee_amount": 5.5}
        )
        self.operation.action_create_refund = "update_quantity"
        self._create_receive_rma()
        self.assertEqual(len(self.sale_order.order_line), 2)
        restocking_fee_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_restocking_fee
        )
        self.assertTrue(restocking_fee_line)
        self.assertEqual(restocking_fee_line.price_subtotal, 5.5)

    def test_4(self):
        """when refund strategy is 'update_quantity' and fee type is percentage-based,
        the fee line is added using the sale line subtotal"""
        self.sale_order.order_line.price_unit = 300
        self.assertEqual(self.sale_order.order_line.price_subtotal, 1500)  # 5 * 300
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "percent", "restocking_fee_amount": 80}
        )
        self.operation.action_create_refund = "update_quantity"
        self._create_receive_rma()
        self.assertEqual(len(self.sale_order.order_line), 2)
        restocking_fee_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_restocking_fee
        )
        self.assertTrue(restocking_fee_line)
        self.assertEqual(restocking_fee_line.price_subtotal, 1200)  # 1500*0.8

    def test_5(self):
        """when refund strategy is 'manual_after_receipt' and fee type is fixed,
        a restocking fee invoice is created with the correct amount, fixed case"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "fixed", "restocking_fee_amount": 5.5}
        )
        self.operation.action_create_refund = "manual_after_receipt"
        rma = self._create_receive_rma()
        self.assertEqual(len(self.sale_order.order_line), 1)
        invoice = rma.restocking_fee_invoice_id
        self.assertTrue(invoice)
        action = rma.action_view_restocking_fee_invoice()
        self.assertEqual(action.get("res_id"), invoice.id)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.price_subtotal, 5.5)

    def test_6(self):
        """when refund strategy is 'manual_after_receipt' and fee type is
        percentage-based, the fee invoice uses the correct percentage of the
        product price"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.product_1.lst_price = 300
        self.operation.write(
            {"restocking_fee_type": "percent", "restocking_fee_amount": 25}
        )
        self.operation.action_create_refund = "manual_after_receipt"
        rma = self.env["rma"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 2,
                "operation_id": self.operation.id,
            }
        )
        rma.action_confirm()
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(rma.reception_move_id.state, "done")
        self.assertEqual(len(self.sale_order.order_line), 1)
        invoice = rma.restocking_fee_invoice_id
        self.assertTrue(invoice)
        action = rma.action_view_restocking_fee_invoice()
        self.assertEqual(action.get("res_id"), invoice.id)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.price_subtotal, 150)  # 300*0.25*2

    def test_7(self):
        """update_quantity, custom restocking fee"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "fixed", "restocking_fee_amount": 5.5}
        )
        self.operation.action_create_refund = "update_quantity"
        rma = self._create_rma()
        rma.write({"restocking_fee_type": "fixed", "restocking_fee_amount": 12.5})
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(rma.reception_move_id.state, "done")
        self.assertEqual(len(self.sale_order.order_line), 2)
        restocking_fee_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_restocking_fee
        )
        self.assertTrue(restocking_fee_line)
        self.assertEqual(restocking_fee_line.price_subtotal, 12.5)

    def test_8(self):
        """invoice manual_after_receipt, custom restocking fee"""
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "fixed", "restocking_fee_amount": 5.5}
        )
        self.operation.action_create_refund = "manual_after_receipt"
        rma = self._create_rma()
        rma.write({"restocking_fee_type": "fixed", "restocking_fee_amount": 12.5})
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(rma.reception_move_id.state, "done")
        self.assertEqual(len(self.sale_order.order_line), 1)
        invoice = rma.restocking_fee_invoice_id
        self.assertTrue(invoice)
        action = rma.action_view_restocking_fee_invoice()
        self.assertEqual(action.get("res_id"), invoice.id)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.price_subtotal, 12.5)

    def test_10(self):
        """when refund strategy is 'update_quantity' and fee type is percentage-based,
        the fee line is added using the sale line subtotal, even if the sale line UoM
        differs from the product UoM
        """
        uom_unit = self.env.ref("uom.product_uom_unit")
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.product_1.uom_id = uom_unit
        sale_line = self.sale_order.order_line
        sale_line.product_uom = uom_dozen
        sale_line.product_uom_qty = 5  # 5 dozens
        sale_line.price_unit = 300
        self.assertEqual(sale_line.price_subtotal, 1500)
        self.assertEqual(len(self.sale_order.order_line), 1)
        self.operation.write(
            {"restocking_fee_type": "percent", "restocking_fee_amount": 10}
        )
        self.operation.action_create_refund = "update_quantity"
        rma = self._create_receive_rma()
        self.assertEqual(rma.product_uom, uom_unit)
        self.assertEqual(rma.product_uom_qty, 5)
        self.assertEqual(sale_line.product_uom, uom_dozen)
        self.assertEqual(sale_line.product_uom_qty, 5)
        self.assertEqual(len(self.sale_order.order_line), 2)
        restocking_fee_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.product_restocking_fee
        )
        self.assertTrue(restocking_fee_line)
        self.assertEqual(
            restocking_fee_line.price_subtotal, 12.5
        )  # (300 /12) * 10% * 5
