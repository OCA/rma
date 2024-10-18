# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.rma_sale.tests.test_rma_sale import TestRmaSaleBase


class TestRmaSaleLot(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "000001", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "000002", "product_id": cls.product.id}
        )
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 1, lot_id=cls.lot_1
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 2, lot_id=cls.lot_2
        )
        cls.sale_order = cls._create_sale_order(cls, [[cls.product, 3]])
        cls.sale_order.action_confirm()
        cls.order_line = cls.sale_order.order_line
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.action_set_quantities_to_reservation()
        cls.order_out_picking._action_done()
        cls.operation = cls.env.ref("rma.rma_operation_replace")

    def test_partial_return(self):
        wizard = self._rma_sale_wizard(self.sale_order)
        line_1 = wizard.line_ids.filtered(
            lambda line, lot=self.lot_1: line.lot_id == lot
        )
        line_2 = wizard.line_ids.filtered(
            lambda line, lot=self.lot_2: line.lot_id == lot
        )
        self.assertEqual(line_1.quantity, 1)
        self.assertEqual(line_2.quantity, 2)
        line_2.quantity = 1
        rma = self.env["rma"].search(wizard.create_and_open_rma()["domain"])
        rma_1 = rma.filtered(lambda r, lot=self.lot_1: r.lot_id == lot)
        rma_2 = rma.filtered(lambda r, lot=self.lot_2: r.lot_id == lot)
        self.assertEqual(rma_1.reception_move_id.restrict_lot_id, self.lot_1)
        self.assertEqual(rma_2.reception_move_id.restrict_lot_id, self.lot_2)
        self.assertEqual(rma_2.product_uom_qty, 1)

    def test_full_return_after_partial_return(self):
        self.test_partial_return()
        wizard = self._rma_sale_wizard(self.sale_order)
        line_1 = wizard.line_ids.filtered(
            lambda line, lot=self.lot_1: line.lot_id == lot
        )
        line_2 = wizard.line_ids.filtered(
            lambda line, lot=self.lot_2: line.lot_id == lot
        )
        self.assertEqual(line_1.quantity, 0)
        self.assertEqual(line_2.quantity, 1)
        rma_2 = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma_2.reception_move_id.restrict_lot_id, self.lot_2)
        self.assertEqual(rma_2.product_uom_qty, 1)
