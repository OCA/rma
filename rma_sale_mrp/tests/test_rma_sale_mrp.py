# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, SavepointCase
from odoo.exceptions import UserError


class TestRmaSaleMrp(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.sale_order = cls.env["sale.order"]
        cls.product_kit = cls.product_product.create({
            "name": "Product test 1",
            "type": "consu",
        })
        cls.product_kit_comp_1 = cls.product_product.create({
            "name": "Product Component 1",
            "type": "product",
        })
        cls.product_kit_comp_2 = cls.product_product.create({
            "name": "Product Component 2",
            "type": "product",
        })
        cls.bom = cls.env["mrp.bom"].create({
            "product_id": cls.product_kit.id,
            "product_tmpl_id": cls.product_kit.product_tmpl_id.id,
            "type": "phantom",
            "bom_line_ids": [
                (0, 0, {
                    "product_id": cls.product_kit_comp_1.id,
                    "product_qty": 2,
                }),
                (0, 0, {
                    "product_id": cls.product_kit_comp_2.id,
                    "product_qty": 4,
                })
            ]})
        cls.product_2 = cls.product_product.create({
            "name": "Product test 2",
            "type": "product",
        })
        cls.partner = cls.res_partner.create({
            "name": "Partner test",
        })
        order_form = Form(cls.sale_order)
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_kit
            line_form.product_uom_qty = 5
        cls.sale_order = order_form.save()
        cls.sale_order.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_kit)
        cls.order_out_picking = cls.sale_order.picking_ids
        # Confirm but leave a backorder to split moves so we can test that
        # the wizard correctly creates the RMAs with the proper quantities
        for line in cls.order_out_picking.move_lines:
            line.quantity_done = line.product_uom_qty - 7
        wiz_act = cls.order_out_picking.button_validate()
        wiz = cls.env["stock.backorder.confirmation"].browse(wiz_act["res_id"])
        wiz.process()
        cls.backorder = cls.sale_order.picking_ids - cls.order_out_picking
        for line in cls.backorder.move_lines:
            line.quantity_done = line.product_uom_qty
        cls.backorder.button_validate()

    def test_create_rma_from_so(self):
        order = self.sale_order
        out_pickings = self.order_out_picking + self.backorder
        wizard_id = order.action_create_rma()["res_id"]
        wizard = self.env["sale.order.rma.wizard"].browse(wizard_id)
        wizard.line_ids.quantity = 4
        res = wizard.create_and_open_rma()
        rmas = self.env["rma"].search(res["domain"])
        for rma in rmas:
            self.assertEqual(rma.partner_id, order.partner_id)
            self.assertEqual(rma.order_id, order)
            self.assertTrue(rma.picking_id in out_pickings)
        self.assertEqual(rmas.mapped("phantom_bom_product"), self.product_kit)
        self.assertEqual(
            rmas.mapped("product_id"),
            self.product_kit_comp_1 + self.product_kit_comp_2
        )
        rma_1 = rmas.filtered(lambda x: x.product_id == self.product_kit_comp_1)
        rma_2 = rmas.filtered(lambda x: x.product_id == self.product_kit_comp_2)
        move_1 = out_pickings.mapped("move_lines").filtered(
            lambda x: x.product_id == self.product_kit_comp_1
        )
        move_2 = out_pickings.mapped("move_lines").filtered(
            lambda x: x.product_id == self.product_kit_comp_2
        )
        self.assertEqual(
            sum(rma_1.mapped("product_uom_qty")),
            8
        )
        self.assertEqual(
            rma_1.mapped("product_uom"),
            move_1.mapped("product_uom")
        )
        self.assertEqual(
            sum(rma_2.mapped("product_uom_qty")),
            16
        )
        self.assertEqual(
            rma_2.mapped("product_uom"),
            move_2.mapped("product_uom")
        )
        self.assertEqual(rma.state, "confirmed")
        self.assertEqual(
            rma_1.mapped("reception_move_id.origin_returned_move_id"),
            move_1,
        )
        self.assertEqual(
            rma_2.mapped("reception_move_id.origin_returned_move_id"),
            move_2,
        )
        self.assertEqual(
            rmas.mapped("reception_move_id.picking_id")
            + self.order_out_picking + self.backorder,
            order.picking_ids,
        )
        # Refund the RMA
        user = self.env["res.users"].create(
            {
                "login": "test_refund_with_so",
                "name": "Test",
            }
        )
        order.user_id = user.id
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id.action_done()
        # All the component RMAs must be received if we want to make a refund
        with self.assertRaises(UserError):
            rma.action_refund()
        rmas_left = rmas - rma
        for additional_rma in rmas_left:
            additional_rma.reception_move_id.quantity_done = (
                additional_rma.product_uom_qty)
            additional_rma.reception_move_id.picking_id.action_done()
        rma.action_refund()
        self.assertEqual(rma.refund_id.user_id, user)
        # The component RMAs get automatically refunded
        self.assertEqual(rma.refund_id, rmas_left.mapped("refund_id"))
        # The refund product is the kit, not the components
        self.assertEqual(
            rma.refund_id.invoice_line_ids.product_id, self.product_kit)
        rma.refund_id.action_invoice_open()
        # We can still return another kit
        wizard_id = order.action_create_rma()["res_id"]
        wizard = self.env["sale.order.rma.wizard"].browse(wizard_id)
        self.assertEqual(wizard.line_ids.quantity, 1)
