# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import Command
from odoo.tests import Form, new_test_user

from odoo.addons.rma.tests.test_rma import TestRma
from odoo.addons.sale.models.sale_order import SaleOrder


class TestProductPrice(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.pricelist_base = cls.env["product.pricelist"].create(
            {
                "name": "Base Pricelist",
            }
        )
        cls.color = cls.env["product.attribute"].create(
            {
                "name": "Color Variant",
            }
        )
        cls.size = cls.env["product.attribute"].create(
            {
                "name": "Size Variant",
            }
        )

        cls.attribute_color_red = cls.env["product.attribute.value"].create(
            {
                "name": "Red",
                "attribute_id": cls.color.id,
            }
        )

        cls.attribute_color_blue = cls.env["product.attribute.value"].create(
            {
                "name": "Blue",
                "attribute_id": cls.color.id,
            }
        )

        cls.attribute_size_m = cls.env["product.attribute.value"].create(
            {
                "name": "M",
                "attribute_id": cls.size.id,
            }
        )

        cls.attribute_size_s = cls.env["product.attribute.value"].create(
            {
                "name": "S",
                "attribute_id": cls.size.id,
            }
        )

        cls.template = cls.env["product.template"].create(
            {
                "name": "Test Product",
                "list_price": 10.0,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.color.id,
                            "value_ids": [
                                Command.link(cls.attribute_color_blue.id),
                                Command.link(cls.attribute_color_red.id),
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.size.id,
                            "value_ids": [
                                Command.link(cls.attribute_size_m.id),
                                Command.link(cls.attribute_size_s.id),
                            ],
                        }
                    ),
                ],
            }
        )
        cls.product_red_s = cls.template.product_variant_ids.filtered(
            lambda p: cls.attribute_color_red.id
            in p.product_template_attribute_value_ids.product_attribute_value_id.ids
            and cls.attribute_size_s.id
            in p.product_template_attribute_value_ids.product_attribute_value_id.ids
        )
        cls.pricelist_base.write(
            {
                "item_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_red_s.id,
                            "applied_on": "0_product_variant",
                            "fixed_price": 6.0,
                        }
                    )
                ]
            }
        )

        cls.product_red_m = cls.template.product_variant_ids.filtered(
            lambda p: cls.attribute_color_red.id
            in p.product_template_attribute_value_ids.product_attribute_value_id.ids
            and cls.attribute_size_m.id
            in p.product_template_attribute_value_ids.product_attribute_value_id.ids
        )
        cls.pricelist_base.write(
            {
                "item_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_red_m.id,
                            "applied_on": "0_product_variant",
                            "fixed_price": 5.0,
                        }
                    )
                ]
            }
        )
        cls.so_model = cls.env["sale.order"]
        cls.env.company.price_display_variant_pricelist_id = cls.pricelist_base

        cls.sale_order = cls._create_sale_order([[cls.product_red_s, 5]])
        cls.sale_order.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_red_s
        )
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity = 5
        cls.order_out_picking.button_validate()

    @classmethod
    def _create_sale_order(cls, products) -> SaleOrder:
        order_form = Form(cls.so_model)
        order_form.partner_id = cls.partner
        for product_info in products:
            with order_form.order_line.new() as line_form:
                line_form.product_id = product_info[0]
                line_form.product_uom_qty = product_info[1]
        return order_form.save()

    @classmethod
    def _rma_sale_wizard(cls, order):
        wizard_id = order.action_create_rma()["res_id"]
        wizard = cls.env["sale.order.rma.wizard"].browse(wizard_id)
        wizard.operation_id = cls.operation
        return wizard

    def test_rma_refund(self):
        self.operation.action_create_refund = "manual_after_receipt"
        self.product_red_s.invoice_policy = "delivery"
        order = self.sale_order
        order._create_invoices()
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertEqual(self.order_line.qty_delivered, 5)
        self.assertEqual(self.order_line.qty_invoiced, 5)
        wizard = self._rma_sale_wizard(order)
        rma = self.env["rma"].browse(wizard.create_and_open_rma()["res_id"])
        self.assertEqual(rma.partner_id, order.partner_id)
        self.assertEqual(rma.order_id, order)
        self.assertEqual(rma.picking_id, self.order_out_picking)
        self.assertEqual(rma.move_id, self.order_out_picking.move_ids)
        self.assertEqual(rma.product_id, self.product_red_s)
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
        self.assertEqual(self.order_line.qty_invoiced, 0)
        self.assertEqual(rma.refund_id.user_id, user)
        self.assertEqual(rma.refund_id.invoice_line_ids.sale_line_ids, self.order_line)
        self.assertEqual(order.invoice_status, "no")

        # Check if price unit is the variant based pricelist one
        self.assertEqual(6.0, rma.refund_line_id.price_unit)
