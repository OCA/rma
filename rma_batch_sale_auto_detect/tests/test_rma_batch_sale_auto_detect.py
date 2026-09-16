# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.rma_sale_auto_detect.tests.common import TestRmaSaleAutoDetectBase


@tagged("-at_install", "post_install")
class TestRmaBatchSaleAutoDetect(TestRmaSaleAutoDetectBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.batch = cls.env["rma.batch"].create({"partner_id": cls.partner.id})

    def _create_rma(self, partner, product, qty, operation):
        rma = super()._create_rma(partner, product, qty, operation)
        rma.batch_id = self.batch
        return rma

    def test_0(self):
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        sale_order2 = self._create_and_confirm_sale_order(
            self.partner, [(self.product2, 5)], 60
        )
        self._process_picking(sale_order2.picking_ids, self.product2, 5)
        rma2 = self._create_rma(self.partner, self.product2, 5, self.operation)
        self.batch.action_ready()
        self.assertEqual(self.batch.state, "manual")
        self.assertTrue(rma.sale_line_id)
        self.assertFalse(rma2.sale_line_id)
        rma2.move_id = sale_order2.order_line.move_ids
        self.batch.action_ready()
        self.assertEqual(self.batch.state, "ready")

    def test_1(self):
        sale_order = self._create_and_confirm_sale_order(
            self.partner, [(self.product, 5)], 30
        )
        self._process_picking(sale_order.picking_ids, self.product, 5)
        rma = self._create_rma(self.partner, self.product, 5, self.operation)
        sale_order2 = self._create_and_confirm_sale_order(
            self.partner, [(self.product2, 5)], 30
        )
        self._process_picking(sale_order2.picking_ids, self.product2, 5)
        rma2 = self._create_rma(self.partner, self.product2, 5, self.operation)
        self.batch.action_ready()
        self.assertEqual(self.batch.state, "ready")
        self.assertTrue(rma.sale_line_id)
        self.assertTrue(rma2.sale_line_id)
