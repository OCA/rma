# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestRmaBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.user
        cls.partner = cls.env["res.partner"].create({"name": "Customer A"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Customer B"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "consu", "is_storable": True}
        )
        cls.loc_stock = cls.env.ref("stock.stock_location_stock")
        cls.loc_customers = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.loc_stock, 100
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product2, cls.loc_stock, 100
        )
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.team = cls.env["rma.team"].create(
            {"name": "Team A", "user_id": cls.user.id}
        )
        cls.tag1 = cls.env["rma.tag"].create({"name": "Tag 1"})
        cls.tag2 = cls.env["rma.tag"].create({"name": "Tag 2"})
        cls.operation = cls.env.ref("rma.rma_operation_replace")

    def _create_and_do_picking(self, lines):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customers.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": product.display_name,
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "location_id": self.loc_stock.id,
                            "location_dest_id": self.loc_customers.id,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def _create_batch(self, lines):
        return self.env["rma.batch"].create(
            {
                "partner_id": self.partner.id,
                "rma_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "operation_id": self.operation.id,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )

    def _return_picking(self, picking, qty):
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
        return_wizard.product_return_moves.quantity = qty
        picking_action = return_wizard.action_create_returns()
        reception = self.env["stock.picking"].browse(picking_action["res_id"])
        return reception

    def test_onchange_sync_rmas_only(self):
        """check that changing batch header fields propagates values to rmas"""
        with Form(self.env["rma.batch"]) as batch_form:
            batch_form.partner_id = self.partner
            batch_form.operation_id = self.operation
            batch_form.user_id = self.user
            batch_form.team_id = self.team
            batch_form.tag_ids.add(self.tag1)
            with batch_form.rma_ids.new() as line:
                line.product_id = self.product
        batch = batch_form.save()
        rma = batch.rma_ids
        self.assertEqual(rma.partner_id, self.partner)
        self.assertEqual(rma.user_id, self.user)
        self.assertEqual(rma.team_id, self.team)
        self.assertEqual(rma.tag_ids, self.tag1)

    def test_change_location_on_batch_propagates_to_rmas(self):
        """check that changing the location on a draft batch updates
        the location on the associated RMAs"""
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        rma_location = warehouse.rma_loc_id
        batch = self._create_batch([(self.product, 5), (self.product2, 3)])
        self.assertEqual(batch.state, "draft")
        batch.location_id = rma_location
        for rma in batch.rma_ids:
            self.assertEqual(rma.location_id, rma_location)

    def test_unlink_forbidden_when_non_draft_rma(self):
        """ensure that a batch can't be deleted if it contains any RMA
        not in draft state"""
        batch = self._create_batch([(self.product, 5)])
        batch.action_ready()
        batch.action_confirm()
        self.assertEqual(batch.rma_ids.state, "confirmed")
        with self.assertRaises(ValidationError):
            batch.unlink()

    def test_states(self):
        """verify the state transitions of a batch and that each transition updates
        the rmas state consistently"""
        batch = self._create_batch([(self.product, 5), (self.product2, 3)])
        batch.action_ready()
        self.assertEqual(batch.state, "ready")

        batch.action_confirm()
        self.assertEqual(batch.state, "confirmed")
        self.assertSetEqual(set(batch.rma_ids.mapped("state")), {"confirmed"})

        batch.action_cancel()
        self.assertEqual(batch.state, "cancelled")
        self.assertSetEqual(set(batch.rma_ids.mapped("state")), {"cancelled"})

        batch.action_draft()
        self.assertEqual(batch.state, "draft")
        self.assertSetEqual(set(batch.rma_ids.mapped("state")), {"draft"})

    def test_return_picking(self):
        """check that returning a picking with a single product and create_rma=True
        creates one rma without generating a batch"""
        picking = self._create_and_do_picking([(self.product, 5)])
        reception = self._return_picking(picking, 5)
        rma = reception.move_ids.rma_receiver_ids
        self.assertFalse(rma.batch_id)

    def test_return_picking_multi_product(self):
        """check that returning a picking with multiple products and create_rma=True
        creates multiple rmas automatically grouped into a new batch"""
        picking = self._create_and_do_picking([(self.product, 5), (self.product2, 5)])
        reception = self._return_picking(picking, 5)
        rma = reception.move_ids.rma_receiver_ids
        self.assertTrue(rma.batch_id)
        self.assertEqual(rma.batch_id.rma_ids.product_id, self.product + self.product2)

    def test_mix_partner(self):
        batch = self._create_batch([(self.product, 5), (self.product2, 5)])
        rma1 = batch.rma_ids[0]
        rma2 = batch.rma_ids[1]
        with self.assertRaisesRegex(
            ValidationError, "All RMAs in a batch must belong to the same partner"
        ):
            rma1.partner_id = self.partner2
        with self.assertRaisesRegex(
            ValidationError, "All RMAs in a batch must belong to the same partner"
        ):
            (rma1 + rma2).partner_id = self.partner2
        batch.partner_id = self.partner2
        self.assertEqual((rma1 + rma2).partner_id, self.partner2)
