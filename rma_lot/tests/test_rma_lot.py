# Copyright 2020 Iryna Vyshnevska Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests.common import Form, TransactionCase


class TestRMALot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_obj = cls.env["stock.picking"]
        partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "000001", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "000002", "product_id": cls.product.id}
        )
        picking_type_out = cls.env.ref("stock.picking_type_out")
        stock_location = cls.env.ref("stock.stock_location_stock")
        customer_location = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 1, lot_id=cls.lot_1
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, stock_location, 2, lot_id=cls.lot_2
        )
        cls.picking = cls.picking_obj.create(
            {
                "partner_id": partner.id,
                "picking_type_id": picking_type_out.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 3,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": stock_location.id,
                            "location_dest_id": customer_location.id,
                        },
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        cls.picking.action_assign()
        cls.picking.move_ids.picked = True
        cls.picking._action_done()
        cls.operation = cls.env.ref("rma.rma_operation_replace")

    @classmethod
    def create_return_wiz(cls):
        return (
            cls.env["stock.return.picking"]
            .with_context(active_id=cls.picking.id, active_model="stock.picking")
            .create({"create_rma": True})
        )

    def test_00(self):
        """
        Check the process of creating RMAs when returning products tracked by lot
            - The correct number of RMAs is created
            - The RMAs are correctly associated with the lot
        """
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=self.picking.ids,
                active_id=self.picking.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking_form.create_rma = True
        return_wizard = stock_return_picking_form.save()
        self.assertEqual(len(return_wizard.product_return_moves), 2)
        return_wizard.create_returns()
        self.assertEqual(self.picking.rma_count, 2)
        rmas = self.picking.move_ids.rma_ids
        rma_lot_1 = rmas.filtered(lambda r, lot=self.lot_1: r.lot_id == lot)
        rma_lot_2 = rmas.filtered(lambda r, lot=self.lot_2: r.lot_id == lot)
        self.assertTrue(rma_lot_1)
        self.assertEqual(rma_lot_1.reception_move_id.restrict_lot_id, self.lot_1)
        self.assertEqual(rma_lot_1.reception_move_id.state, "assigned")
        self.assertEqual(rma_lot_1.reception_move_id.move_line_ids.lot_id, self.lot_1)
        self.assertTrue(rma_lot_2)
        self.assertEqual(rma_lot_2.reception_move_id.restrict_lot_id, self.lot_2)
        self.assertEqual(rma_lot_2.reception_move_id.state, "assigned")
        self.assertEqual(rma_lot_2.reception_move_id.move_line_ids.lot_id, self.lot_2)

    def test_rma_form(self):
        rma_form = Form(self.env["rma"])
        self.assertFalse(rma_form.product_id)
        rma_form.lot_id = self.lot_1
        self.assertEqual(rma_form.product_id, self.product)
        rma_form.product_id = self.env.ref("product.product_product_4")
        self.assertFalse(rma_form.lot_id)
