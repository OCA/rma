# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaProcurementCustomer(TestRma):
    def _create_delivery(self):
        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                "|",
                ("warehouse_id.company_id", "=", self.company.id),
                ("warehouse_id", "=", False),
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env["stock.picking"].with_context(
                default_picking_type_id=picking_type.id
            ),
            view="stock.view_picking_form",
        )
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product
            move.product_uom_qty = 10
        picking = picking_form.save()
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        return picking

    def _return_picking_with_rma(self, picking):
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking_form.create_rma = True
        stock_return_picking_form.rma_operation_id = self.operation
        return_wizard = stock_return_picking_form.save()
        return_wizard.create_returns()
        origin_move = picking.move_ids
        return origin_move.rma_ids

    def _create_replace_picking(self, rma):
        res = rma.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product
        wizard_form.product_uom_qty = rma.product_uom_qty
        wizard = wizard_form.save()
        wizard.action_deliver()
        return rma.mapped("delivery_move_ids.picking_id")

    def test_0(self):
        customer = self.partner.copy()
        origin_delivery = self._create_delivery()
        origin_delivery.customer_id = customer
        rma = self._return_picking_with_rma(origin_delivery)
        reception_move = rma.reception_move_id
        reception = reception_move.picking_id
        reception_move.quantity_done = reception_move.product_uom_qty
        reception._action_done()
        out_pickings = self._create_replace_picking(rma)
        self.assertEqual(reception.customer_id, customer)
        self.assertEqual(out_pickings.customer_id, customer)
