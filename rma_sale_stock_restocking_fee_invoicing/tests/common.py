# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.rma_sale.tests.test_rma_sale import TestRmaSaleBase


class TestRmaSaleStockRestockingFeeInvoicingCommon(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls._create_sale_order([[cls.product_1, 5]])
        cls.sale_order.action_confirm()
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_1
        )
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity = 5
        cls.order_out_picking.button_validate()
        cls.product_restocking_fee = cls.env.ref(
            "sale_stock_restocking_fee_invoicing.product_restocking_fee"
        )

    def _create_rma(self, rma_operation=None):
        wizard = self._rma_sale_wizard(self.sale_order)
        if rma_operation:
            wizard.operation_id = rma_operation
            wizard.line_ids.write({"operation_id": rma_operation})
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertTrue(rma.reception_move_id)
        return rma

    def _create_receive_rma(self):
        rma = self._create_rma()
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(rma.reception_move_id.state, "done")
        return rma
