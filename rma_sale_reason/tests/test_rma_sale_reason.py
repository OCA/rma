# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests.common import users

from odoo.addons.rma_sale.tests.test_rma_sale import TestRmaSaleBase


class TestRmaSaleReason(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rma_reason = cls.env.ref("rma_reason.rma_reason_defective_product")
        cls.operation = cls.rma_operation_model.sudo().search([], limit=1)
        cls.sale_order = cls._create_sale_order(cls, [[cls.product_1, 5]])
        cls.sale_order.action_confirm()
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_1
        )
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity_done = 5
        cls.order_out_picking.button_validate()

    def _create_wizard(self):
        order = self.sale_order.sudo()
        wizard_id = order.action_create_rma()["res_id"]
        wizard = self.env["sale.order.rma.wizard"].sudo().browse(wizard_id)
        wizard.operation_id = self.operation
        return wizard

    @users("partner@rma.example.com")
    def test_create_rma_from_wizard(self):
        order = self.sale_order
        wizard = self._create_wizard()
        self.assertFalse(wizard.reason_id)
        self.assertFalse(wizard.line_ids.reason_id)
        wizard.reason_id = self.rma_reason
        self.assertEqual(wizard.line_ids.reason_id, self.rma_reason)
        rma = wizard.sudo().create_rma(from_portal=True)
        self.assertEqual(rma.order_id, order)
        self.assertEqual(rma.reason_id, self.rma_reason)
