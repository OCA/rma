# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2022-2025 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, new_test_user
from odoo.tests.common import users
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestRmaSaleBase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.so_model = cls.env["sale.order"]

        cls.product_1 = cls.product_product.create(
            {"name": "Product test 1", "type": "consu", "is_storable": True}
        )
        cls.product_2 = cls.product_product.create(
            {"name": "Product test 2", "type": "consu", "is_storable": True}
        )
        cls.partner = cls.res_partner.create(
            {"name": "Partner test", "email": "partner@rma"}
        )
        cls.report_model = cls.env["ir.actions.report"]
        cls.rma_operation_model = cls.env["rma.operation"]
        cls.operation = cls.env.ref("rma.rma_operation_replace")
        cls._partner_portal_wizard(cls.partner)
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_1, cls.wh.lot_stock_id, 20
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_2, cls.wh.lot_stock_id, 20
        )

    @classmethod
    def _create_sale_order(cls, products):
        order_form = Form(cls.so_model)
        order_form.partner_id = cls.partner
        for product_info in products:
            with order_form.order_line.new() as line_form:
                line_form.product_id = product_info[0]
                line_form.product_uom_qty = product_info[1]
        return order_form.save()

    @classmethod
    def _partner_portal_wizard(cls, partner):
        wizard_all = (
            cls.env["portal.wizard"]
            .with_context(**{"active_ids": [partner.id]})
            .create({})
        )
        wizard_all.user_ids.action_grant_access()

    @classmethod
    def _rma_sale_wizard(cls, order):
        wizard_id = order.action_create_rma()["res_id"]
        wizard = cls.env["sale.order.rma.wizard"].browse(wizard_id)
        wizard.operation_id = cls.operation
        return wizard


class TestRmaSale(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls._create_sale_order([[cls.product_1, 5]])
        cls.sale_order.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_1
        )
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity = 5
        cls.order_out_picking.button_validate()

    def test_rma_sale_computes_onchange(self):
        rma = self.env["rma"].new()
        # No m2m values when everything is selectable
        self.assertFalse(rma.allowed_picking_ids)
        self.assertFalse(rma.allowed_move_ids)
        self.assertFalse(rma.allowed_product_ids)
        # Partner selected
        rma.order_id = self.sale_order
        rma.partner_id = self.partner
        self.assertFalse(rma.order_id)
        self.assertEqual(rma.allowed_picking_ids._origin, self.order_out_picking)
        # Order selected
        rma.order_id = self.sale_order
        self.assertEqual(rma.allowed_picking_ids._origin, self.order_out_picking)
        rma.picking_id = self.order_out_picking
        self.assertEqual(rma.allowed_move_ids._origin, self.order_out_picking.move_ids)
        self.assertEqual(rma.allowed_product_ids._origin, self.product_1)
        # Onchanges
        rma.product_id = self.product_1
        rma._onchange_order_id()
        self.assertFalse(rma.product_id)
        self.assertFalse(rma.picking_id)

    def test_create_rma_with_so(self):
        rma_vals = {
            "partner_id": self.partner.id,
            "order_id": self.sale_order.id,
            "product_id": self.product_1.id,
            "product_uom_qty": 5,
            "location_id": self.sale_order.warehouse_id.rma_loc_id.id,
            "operation_id": self.operation.id,
        }
        rma = self.env["rma"].create(rma_vals)
        rma.action_confirm()
        self.assertTrue(rma.reception_move_id)
        self.assertFalse(rma.reception_move_id.origin_returned_move_id)
        # Receive the product
        rma.reception_move_id.quantity = rma.product_uom_qty
        rma.reception_move_id.picking_id.button_validate()
        # Now do a replacement for testing the issue of a new SO line created for P2
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids, rma_delivery_type="replace"
            )
        )
        delivery_form.product_id = self.product_2
        delivery_form.product_uom_qty = 5
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        rma.delivery_move_ids.quantity = rma.product_uom_qty
        rma.delivery_move_ids.picking_id.button_validate()
        self.assertEqual(len(self.sale_order.order_line), 1)

    @mute_logger("odoo.models.unlink")
    def test_create_rma_from_so(self):
        order = self.sale_order
        wizard = self._rma_sale_wizard(order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma.partner_id, order.partner_id)
        self.assertEqual(rma.order_id, order)
        self.assertEqual(rma.picking_id, self.order_out_picking)
        self.assertEqual(rma.move_id, self.order_out_picking.move_ids)
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_uom_qty, self.order_line.product_uom_qty)
        self.assertEqual(rma.product_uom, self.order_line.product_uom)
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(
            rma.reception_move_id.origin_returned_move_id,
            self.order_out_picking.move_ids,
        )
        self.assertEqual(
            rma.reception_move_id.picking_id + self.order_out_picking,
            order.picking_ids,
        )
        user = new_test_user(self.env, login="test_refund_with_so")
        order.user_id = user.id
        # Receive the RMA
        rma.action_confirm()
        rma.reception_move_id.quantity = rma.product_uom_qty
        rma.reception_move_id.picking_id.button_validate()
        # Refund the RMA
        rma.action_refund()
        self.assertEqual(self.order_line.qty_delivered, 0)
        self.assertEqual(self.order_line.qty_invoiced, -5)
        self.assertEqual(rma.refund_id.user_id, user)
        self.assertEqual(rma.refund_id.invoice_line_ids.sale_line_ids, self.order_line)
        # Cancel the refund
        rma.refund_id.button_cancel()
        self.assertEqual(self.order_line.qty_delivered, 5)
        self.assertEqual(self.order_line.qty_invoiced, 0)
        # And put it to draft again
        rma.refund_id.button_draft()
        self.assertEqual(self.order_line.qty_delivered, 0)
        self.assertEqual(self.order_line.qty_invoiced, -5)

    @users("partner@rma")
    def test_create_rma_from_so_portal_user(self):
        order = self.sale_order
        wizard_obj = (
            self.env["sale.order.rma.wizard"].sudo().with_context(active_id=order.id)
        )
        operation = self.rma_operation_model.sudo().search([], limit=1)
        line_vals = [
            Command.create(
                {
                    "product_id": order.order_line.product_id.id,
                    "sale_line_id": order.order_line.id,
                    "quantity": order.order_line.product_uom_qty,
                    "allowed_quantity": order.order_line.qty_delivered,
                    "uom_id": order.order_line.product_uom.id,
                    "picking_id": order.picking_ids[0].id,
                    "operation_id": operation.id,
                },
            )
        ]
        wizard = wizard_obj.create(
            {
                "line_ids": line_vals,
                "location_id": order.warehouse_id.rma_loc_id.id,
            }
        )
        rma = wizard.sudo().create_rma(from_portal=True)
        self.assertEqual(rma.order_id, order)
        self.assertIn(order.partner_id, rma.message_partner_ids)
        self.assertEqual(order.rma_count, 1)

    def test_create_recurrent_rma(self):
        """An RMA of a product that had an RMA in the past should be possible"""
        wizard = self._rma_sale_wizard(self.sale_order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        rma.reception_move_id.quantity = rma.product_uom_qty
        rma.reception_move_id.picking_id.button_validate()
        wizard = self._rma_sale_wizard(self.sale_order)
        self.assertEqual(
            wizard.line_ids.quantity,
            0,
            "There shouldn't be any allowed quantities for RMAs",
        )
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_form.product_uom_qty = rma.product_uom_qty
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        picking = rma.delivery_move_ids.picking_id
        picking.move_ids.quantity = rma.product_uom_qty
        picking.button_validate()
        # The product is returned to the customer, so we should be able to make
        # another RMA in the future
        wizard = self._rma_sale_wizard(self.sale_order)
        self.assertEqual(
            wizard.line_ids.quantity,
            rma.product_uom_qty,
            "We should be allowed to return the product again",
        )

    def test_report_rma(self):
        wizard = self._rma_sale_wizard(self.sale_order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        operation = self.rma_operation_model.sudo().search([], limit=1)
        rma.operation_id = operation.id
        res = self.env["ir.actions.report"]._render_qweb_html("rma.report_rma", rma.ids)
        res = str(res[0])
        self.assertRegex(res, self.sale_order.name)
        self.assertRegex(res, operation.name)

    def test_manual_refund_no_quantity_impact(self):
        """If the operation is meant for a manual refund, the delivered quantity
        should not be updated."""
        self.operation.action_create_refund = "manual_after_receipt"
        order = self.sale_order
        order_line = order.order_line
        self.assertEqual(order_line.qty_delivered, 5)
        wizard = self._rma_sale_wizard(order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertFalse(rma.reception_move_id.sale_line_id)
        rma.action_confirm()
        rma.reception_move_id._set_quantity_done(rma.product_uom_qty)
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(order.order_line.qty_delivered, 5)

    def test_no_manual_refund_quantity_impact(self):
        """If the operation is meant for a manual refund, the delivered quantity
        should not be updated."""
        self.operation.action_create_refund = "update_quantity"
        order = self.sale_order
        order_line = order.order_line
        self.assertEqual(order_line.qty_delivered, 5)
        wizard = self._rma_sale_wizard(order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma.reception_move_id.sale_line_id, order_line)
        self.assertFalse(rma.can_be_refunded)
        rma.reception_move_id._set_quantity_done(rma.product_uom_qty)
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(order.order_line.qty_delivered, 0)
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_form.product_uom_qty = rma.product_uom_qty
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        picking = rma.delivery_move_ids.picking_id
        picking.move_ids._set_quantity_done(rma.product_uom_qty)
        picking.button_validate()
        self.assertEqual(order.order_line.qty_delivered, 5)

    def test_grouping_reception(self):
        sale_order = self._create_sale_order([[self.product_1, 5], [self.product_2, 5]])
        sale_order.action_confirm()
        sale_order.picking_ids.move_ids.quantity = 5
        sale_order.picking_ids.button_validate()
        wizard = self._rma_sale_wizard(sale_order)
        rmas = self.env["rma"].search(wizard.create_and_open_rma()["domain"])
        self.assertEqual(len(rmas.reception_move_id.group_id), 1)
        self.assertEqual(len(rmas.reception_move_id.picking_id), 1)

    def test_return_different_product(self):
        self.operation.action_create_delivery = False
        self.operation.different_return_product = True
        self.operation.action_create_refund = "update_quantity"
        order = self.sale_order
        order_line = order.order_line
        self.assertEqual(order_line.qty_delivered, 5)
        wizard = self._rma_sale_wizard(order)
        with self.assertRaises(
            ValidationError, msg="Complete the replacement information"
        ):
            rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        return_product = self.product_product.create(
            {"name": "return Product test 1", "type": "consu", "is_storable": True}
        )
        wizard.line_ids.return_product_id = return_product
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma.reception_move_id.sale_line_id, order_line)
        self.assertEqual(rma.reception_move_id.product_id, return_product)
        self.assertFalse(rma.can_be_refunded)
        rma.reception_move_id._set_quantity_done(rma.product_uom_qty)
        rma.reception_move_id.picking_id.button_validate()
        self.assertEqual(order.order_line.qty_delivered, 5)

    def test_reception_grouped_even_from_different_sale_order(self):
        """
        ensure that RMAs linked to different sale orders are grouped and the procurement
        group is not linked to any of the so
        """
        sale_order1 = self._create_sale_order([[self.product_1, 5]])
        sale_order1.action_confirm()
        sale_order1.picking_ids.move_ids.quantity = 5
        sale_order1.picking_ids.button_validate()
        rma1 = self.env["rma"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 5,
                "move_id": sale_order1.order_line.move_ids.id,
                "order_id": sale_order1.id,
                "operation_id": self.operation.id,
            }
        )
        sale_order2 = self._create_sale_order([[self.product_1, 5]])
        sale_order2.action_confirm()
        sale_order2.picking_ids.move_ids.quantity = 5
        sale_order2.picking_ids.button_validate()
        rma2 = self.env["rma"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 5,
                "move_id": sale_order2.order_line.move_ids.id,
                "order_id": sale_order2.id,
                "operation_id": self.operation.id,
            }
        )
        (rma1 + rma2).action_confirm()

        self.assertEqual(
            rma1.reception_move_id.picking_id, rma2.reception_move_id.picking_id
        )
        self.assertFalse(rma1.procurement_group_id.sale_id)

    def test_reception_grouped_from_same_sale_order(self):
        """
        ensure that RMAs linked to same sale orders are grouped and the procurement
        group is linked to the so
        """
        sale_order = self._create_sale_order([[self.product_1, 5], [self.product_2, 5]])
        sale_order.action_confirm()
        sale_order.picking_ids.move_ids.quantity = 5
        sale_order.picking_ids.button_validate()
        sale_line1 = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product_1
        )
        sale_line2 = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product_2
        )
        rma1 = self.env["rma"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_1.id,
                "product_uom_qty": 5,
                "move_id": sale_line1.move_ids.id,
                "order_id": sale_order.id,
                "operation_id": self.operation.id,
            }
        )
        rma2 = self.env["rma"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_2.id,
                "product_uom_qty": 5,
                "move_id": sale_line2.move_ids.id,
                "order_id": sale_order.id,
                "operation_id": self.operation.id,
            }
        )
        (rma1 + rma2).action_confirm()

        self.assertEqual(
            rma1.reception_move_id.picking_id, rma2.reception_move_id.picking_id
        )
        self.assertEqual(rma1.procurement_group_id.sale_id, sale_order)
