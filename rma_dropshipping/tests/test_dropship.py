# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common

from odoo.addons.rma.tests.test_rma import TestRma


@common.tagged("post_install", "-at_install")
class TestDropship(TestRma):
    def test_dropship(self):
        supplier = self.env["res.partner"].create({"name": "Vendor"})
        dropshipping_route = self.env.ref("stock_dropshipping.route_drop_shipping")
        product = self.env["product.product"].create(
            {
                "name": "Test",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_1").id,
                "lst_price": 1000.0,
                "standard_price": 0.0,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "route_ids": [(6, 0, dropshipping_route.ids)],
                "seller_ids": [
                    (0, 0, {"delay": 1, "name": supplier.id, "min_qty": 2.0})
                ],
            }
        )
        partner = self.env["res.partner"].create({"name": "Partner"})
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = partner
        so_form.payment_term_id = self.env.ref(
            "account.account_payment_term_end_following_month"
        )
        with so_form.order_line.new() as line:
            line.product_id = product
            line.product_uom_qty = 10
            line.price_unit = 1.00
        sale_order = so_form.save()
        sale_order.action_confirm()

        purchase = self.env["purchase.order"].search([("partner_id", "=", supplier.id)])
        purchase.button_confirm()

        purchase.picking_ids.move_lines.quantity_done = (
            purchase.picking_ids.move_lines.product_qty
        )
        purchase.picking_ids.button_validate()

        rma = self._create_confirm_receive(partner, product, 10, self.rma_loc)
        delivery_form = Form(
            self.env["rma.delivery.wizard"].with_context(
                active_ids=rma.ids,
                rma_delivery_type="return",
            )
        )
        delivery_form.product_uom_qty = 10
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()

        purchase = (
            self.env["purchase.order"].search([("partner_id", "=", supplier.id)])
            - purchase
        )
        purchase_rma = purchase.order_line.rma_id
        self.assertEqual(purchase_rma, rma)
        purchase.button_confirm()
        self.assertEqual(purchase.picking_ids.move_lines.rma_id, rma)
        self.assertTrue(purchase.picking_ids in rma.delivery_move_ids.picking_id)
