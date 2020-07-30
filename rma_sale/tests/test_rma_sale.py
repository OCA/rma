# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase


class TestRmaSale(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaSale, cls).setUpClass()
        cls.res_partner = cls.env['res.partner']
        cls.product_product = cls.env['product.product']
        cls.sale_order = cls.env['sale.order']

        cls.product_1 = cls.product_product.create({
            'name': 'Product test 1',
            'type': 'product',
        })
        cls.product_2 = cls.product_product.create({
            'name': 'Product test 2',
            'type': 'product',
        })
        cls.partner = cls.res_partner.create({
            'name': 'Partner test',
        })
        order_form = Form(cls.sale_order)
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 5
        cls.sale_order = order_form.save()
        cls.sale_order.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_1)
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_lines.quantity_done = 5
        cls.order_out_picking.button_validate()

    def test_create_rma_with_so(self):
        rma_form = Form(self.env['rma'])
        rma_form.partner_id = self.partner
        rma_form.order_id = self.sale_order
        rma_form.product_id = self.product_1
        rma_form.product_uom_qty = 5
        rma = rma_form.save()
        rma.action_confirm()
        self.assertTrue(rma.reception_move_id)
        self.assertFalse(rma.reception_move_id.origin_returned_move_id)

    def test_create_rma_from_so(self):
        order = self.sale_order
        wizard_id = order.action_create_rma()['res_id']
        wizard = self.env['sale.order.rma.wizard'].browse(wizard_id)
        rma = self.env['rma'].browse(wizard.create_and_open_rma()['res_id'])
        self.assertEqual(rma.partner_id, order.partner_id)
        self.assertEqual(rma.order_id, order)
        self.assertEqual(rma.picking_id, self.order_out_picking)
        self.assertEqual(rma.move_id, self.order_out_picking.move_lines)
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_uom_qty, self.order_line.product_uom_qty)
        self.assertEqual(rma.product_uom, self.order_line.product_uom)
        self.assertEqual(rma.state, 'confirmed')
        self.assertEqual(
            rma.reception_move_id.origin_returned_move_id,
            self.order_out_picking.move_lines,
        )
        self.assertEqual(
            rma.reception_move_id.picking_id + self.order_out_picking,
            order.picking_ids,
        )
