# Copyright 2020 Iryna Vyshnevska Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestRMALot(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_obj = cls.env["stock.picking"]
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "test_product",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.product_extra = cls.env["product.product"].create(
            {
                "name": "test_product extra",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "000001", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "000002", "product_id": cls.product.id}
        )
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.lot_extra = cls.env["stock.lot"].create(
            {"name": "000003", "product_id": cls.product_extra.id}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 1, lot_id=cls.lot_1
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 2, lot_id=cls.lot_2
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_extra, cls.stock_location, 1, lot_id=cls.lot_extra
        )
        cls.picking = cls.picking_obj.create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_out.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 3,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": cls.stock_location.id,
                            "location_dest_id": cls.customer_location.id,
                        },
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        cls.picking.action_assign()
        cls.picking.button_validate()
        cls.operation = cls.env.ref("rma.rma_operation_replace")
        cls.operation.action_create_delivery = "automatic_on_confirm"

    @classmethod
    def create_return_wiz(cls, picking):
        return (
            cls.env["stock.return.picking"]
            .with_context(active_id=picking.id, active_model="stock.picking")
            .create({"create_rma": True})
        )

    def _create_rmas(self, picking, lot_1, lot_2):
        """
        Check the process of creating RMAs when returning products tracked by lot
            - The correct number of RMAs is created
            - The RMAs are correctly associated with the lot
        """
        return_wizard = self.create_return_wiz(picking)
        return_wizard.create_rma = True
        return_wizard.rma_operation_id = self.operation
        self.assertEqual(len(return_wizard.product_return_moves), 2)
        return_wizard.action_create_returns_all()
        self.assertEqual(picking.rma_count, 2)
        rmas = picking.move_ids.rma_ids
        rma_lot_1 = rmas.filtered(lambda r, lot=lot_1: r.lot_id == lot)
        self.assertTrue(rma_lot_1)
        rma_lot_2 = rmas.filtered(lambda r, lot=lot_2: r.lot_id == lot)
        self.assertTrue(rma_lot_2)
        return rma_lot_1, rma_lot_2

    def test_00(self):
        """
        Check the process of creating RMAs when returning products tracked by lot
            - The correct number of RMAs is created
            - The RMAs are correctly associated with the lot
        """
        rma_lot_1, rma_lot_2 = self._create_rmas(self.picking, self.lot_1, self.lot_2)
        self.assertEqual(rma_lot_1.product_uom_qty, 1)
        self.assertEqual(rma_lot_1.reception_move_id.restrict_lot_id, self.lot_1)
        self.assertEqual(rma_lot_1.reception_move_id.state, "assigned")
        self.assertEqual(rma_lot_2.product_uom_qty, 2)
        self.assertEqual(rma_lot_2.reception_move_id.restrict_lot_id, self.lot_2)
        self.assertEqual(rma_lot_2.reception_move_id.state, "assigned")

    def test_01(self):
        lot_3 = self.env["stock.lot"].create(
            {"name": "000003", "product_id": self.product.id}
        )
        lot_4 = self.env["stock.lot"].create(
            {"name": "000004", "product_id": self.product.id}
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 1, lot_id=lot_3
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 2, lot_id=lot_4
        )
        picking = self.picking_obj.create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "restrict_lot_id": lot_3.id,
                        },
                    ),
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "restrict_lot_id": lot_4.id,
                        },
                    ),
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        rma_lot_3, rma_lot_4 = self._create_rmas(picking, lot_3, lot_4)
        self.assertEqual(rma_lot_3.product_uom_qty, 1)
        self.assertEqual(rma_lot_3.reception_move_id.restrict_lot_id, lot_3)
        self.assertEqual(rma_lot_3.reception_move_id.state, "assigned")
        self.assertEqual(rma_lot_4.product_uom_qty, 2)
        self.assertEqual(rma_lot_4.reception_move_id.restrict_lot_id, lot_4)
        self.assertEqual(rma_lot_4.reception_move_id.state, "assigned")

    def test_rma_form(self):
        rma_form = Form(self.env["rma"])
        self.assertFalse(rma_form.product_id)
        rma_form.lot_id = self.lot_1
        self.assertEqual(rma_form.product_id, self.product)
        rma_form.product_id = self.env.ref("product.product_product_4")
        self.assertFalse(rma_form.lot_id)

    def test_deliver_same_lot_as_received(self):
        self.operation.deliver_same_lot = True
        rma_lot_1, rma_lot_2 = self._create_rmas(self.picking, self.lot_1, self.lot_2)
        self.assertEqual(rma_lot_1.delivery_move_ids.restrict_lot_id, self.lot_1)
        self.assertEqual(rma_lot_2.delivery_move_ids.restrict_lot_id, self.lot_2)

    @mute_logger("odoo.models.unlink")
    def test_deliver_same_lot_as_received_extra(self):
        self.operation.deliver_same_lot = True
        self.operation.action_create_delivery = "manual_after_receipt"
        rma_lot_1, rma_lot_2 = self._create_rmas(self.picking, self.lot_1, self.lot_2)
        reception_picking = rma_lot_1.reception_move_id.picking_id
        reception_picking.button_validate()
        self.assertEqual(reception_picking.state, "done")
        self.assertEqual(rma_lot_1.state, "received")
        self.assertEqual(rma_lot_2.state, "received")
        rma_lot_1.lot_id = self.lot_2
        rma_lot_1.create_return(
            fields.Datetime.now(),
            rma_lot_1.product_uom_qty,
            rma_lot_1.product_uom,
        )
        delivery_picking = rma_lot_1.delivery_move_ids.picking_id
        self.assertEqual(delivery_picking.state, "assigned")
        delivery_picking.button_validate()
        self.assertEqual(delivery_picking.state, "done")

    def test_deliver_different_lot_as_received(self):
        self.operation.deliver_same_lot = False
        rma_lot_1, rma_lot_2 = self._create_rmas(self.picking, self.lot_1, self.lot_2)
        self.assertFalse(rma_lot_1.delivery_move_ids.restrict_lot_id)
        self.assertFalse(rma_lot_2.delivery_move_ids.restrict_lot_id, self.lot_2)

    def test_replace_wizard_lot_change(self):
        self.operation.action_create_delivery = "manual_after_receipt"
        rma_lot_1, rma_lot_2 = self._create_rmas(self.picking, self.lot_1, self.lot_2)
        reception_picking = rma_lot_1.reception_move_id.picking_id
        reception_picking.button_validate()
        self.assertEqual(reception_picking.state, "done")
        self.assertEqual(rma_lot_1.state, "received")
        self.assertEqual(rma_lot_2.state, "received")
        res = rma_lot_1.action_replace()
        wizard_form = Form(self.env[res["res_model"]].with_context(**res["context"]))
        wizard_form.product_id = self.product_extra
        wizard_form.lot_id = self.lot_extra
        wizard = wizard_form.save()
        wizard.action_deliver()
        self.assertEqual(rma_lot_1.state, "waiting_replacement")
        self.assertEqual(rma_lot_1.delivery_move_ids.product_id, self.product_extra)
        self.assertEqual(rma_lot_1.delivery_move_ids.restrict_lot_id, self.lot_extra)
