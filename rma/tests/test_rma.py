# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase
from odoo.exceptions import UserError, ValidationError


class TestRma(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestRma, cls).setUpClass()
        cls.res_partner = cls.env['res.partner']
        cls.product_product = cls.env['product.product']
        cls.company = cls.env.user.company_id
        cls.warehouse_company = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.rma_loc = cls.warehouse_company.rma_loc_id
        account_pay = cls.env['account.account'].create({
            'code': 'X1111',
            'name': 'Creditors - (test)',
            'user_type_id': cls.env.ref(
                'account.data_account_type_payable').id,
            'reconcile': True,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'sale_0',
            'code': 'SALE0',
            'type': 'sale',
            'default_debit_account_id': account_pay.id,
        })
        cls.product = cls.product_product.create({
            'name': 'Product test 1',
            'type': 'product',
        })
        account_type = cls.env['account.account.type'].create({
            'name': 'RCV type',
            'type': 'receivable',
        })
        cls.account_receiv = cls.env['account.account'].create({
            'name': 'Receivable',
            'code': 'RCV00',
            'user_type_id': account_type.id,
            'reconcile': True,
        })
        cls.partner = cls.res_partner.create({
            'name': 'Partner test',
            'property_account_receivable_id': cls.account_receiv.id,
        })
        cls.partner_invoice = cls.res_partner.create({
            'name': 'Partner invoice test',
            'parent_id': cls.partner.id,
            'type': 'invoice',
        })
        cls.partner_shipping = cls.res_partner.create({
            'name': 'Partner shipping test',
            'parent_id': cls.partner.id,
            'type': 'delivery',
        })

    def _create_rma(self, partner=None, product=None, qty=None, location=None):
        rma_form = Form(self.env['rma'])
        if partner:
            rma_form.partner_id = partner
        if product:
            rma_form.product_id = product
        if qty:
            rma_form.product_uom_qty = qty
        if location:
            rma_form.location_id = location
        return rma_form.save()

    def _create_confirm_receive(self, partner=None, product=None, qty=None,
                                location=None):
        rma = self._create_rma(partner, product, qty, location)
        rma.action_confirm()
        rma.reception_move_id.quantity_done = rma.product_uom_qty
        rma.reception_move_id.picking_id.action_done()
        return rma

    def _test_readonly_fields(self, rma):
        with Form(rma) as rma_form:
            with self.assertRaises(AssertionError):
                rma_form.partner_id = self.env['res.partner']
            with self.assertRaises(AssertionError):
                rma_form.partner_invoice_id = self.env['res.partner']
            with self.assertRaises(AssertionError):
                rma_form.picking_id = self.env['stock.picking']
            with self.assertRaises(AssertionError):
                rma_form.move_id = self.env['stock.move']
            with self.assertRaises(AssertionError):
                rma_form.product_id = self.env['product.product']
            with self.assertRaises(AssertionError):
                rma_form.product_uom_qty = 0
            with self.assertRaises(AssertionError):
                rma_form.product_uom = self.env['uom.uom']
            with self.assertRaises(AssertionError):
                rma_form.location_id = self.env['stock.location']

    def _create_delivery(self):
        picking_type = self.env['stock.picking.type'].search(
            [
                ('code', '=', 'outgoing'),
                '|',
                ('warehouse_id.company_id', '=', self.company.id),
                ('warehouse_id', '=', False)
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env['stock.picking'].with_context(
                default_picking_type_id=picking_type.id),
            view="stock.view_picking_form",
        )
        picking_form.company_id = self.company
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product
            move.product_uom_qty = 10
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_product.create(
                {'name': 'Product 2 test', 'type': 'product'})
            move.product_uom_qty = 20
        picking = picking_form.save()
        picking.action_confirm()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        return picking

    def test_onchange(self):
        rma_form = Form(self.env['rma'])
        # If partner changes, the invoice address is set
        rma_form.partner_id = self.partner
        self.assertEqual(rma_form.partner_invoice_id, self.partner_invoice)
        # If origin move changes, the product is set
        uom_ten = self.env['uom.uom'].create({
            'name': "Ten",
            'category_id': self.env.ref('uom.product_uom_unit').id,
            'factor_inv': 10,
            'uom_type': 'bigger',
        })
        product_2 = self.product_product.create({
            'name': 'Product test 2',
            'type': 'product',
            'uom_id': uom_ten.id,
        })
        outgoing_picking_type = self.env['stock.picking.type'].search(
            [
                ('code', '=', 'outgoing'),
                '|',
                ('warehouse_id.company_id', '=', self.company.id),
                ('warehouse_id', '=', False)
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env['stock.picking'].with_context(
                default_picking_type_id=outgoing_picking_type.id),
            view="stock.view_picking_form",
        )
        picking_form.company_id = self.company
        picking_form.partner_id = self.partner
        picking_form.partner_id = self.partner
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = product_2
            move.product_uom_qty = 15
            move.product_uom = uom_ten
        picking = picking_form.save()
        picking.action_done()
        rma_form.picking_id = picking
        rma_form.move_id = picking.move_lines
        self.assertEqual(rma_form.product_id, product_2)
        self.assertEqual(rma_form.product_uom_qty, 15)
        self.assertEqual(rma_form.product_uom, uom_ten)
        # If product changes, unit of measure changes
        rma_form.picking_id = self.env['stock.picking']
        rma_form.product_id = self.product
        self.assertEqual(rma_form.product_id, self.product)
        self.assertEqual(rma_form.product_uom_qty, 15)
        self.assertNotEqual(rma_form.product_uom, uom_ten)
        self.assertEqual(rma_form.product_uom, self.product.uom_id)
        rma = rma_form.save()
        # If product changes, unit of measure domain should also change
        domain = rma._onchange_product_id()['domain']['product_uom']
        self.assertListEqual(
            domain, [('category_id', '=', self.product.uom_id.category_id.id)])

    def test_ensure_required_fields_on_confirm(self):
        rma = self._create_rma()
        with self.assertRaises(ValidationError) as e:
            rma.action_confirm()
        self.assertEqual(
            e.exception.name,
            "Required field(s):\nCustomer\nInvoice Address\n"
            "Shipping Address\nProduct\nLocation"
        )
        with Form(rma) as rma_form:
            rma_form.partner_id = self.partner
        with self.assertRaises(ValidationError) as e:
            rma.action_confirm()
        self.assertEqual(
            e.exception.name, "Required field(s):\nProduct\nLocation")
        with Form(rma) as rma_form:
            rma_form.product_id = self.product
            rma_form.location_id = self.rma_loc
        rma.action_confirm()
        self.assertEqual(rma.state, 'confirmed')

    def test_confirm_and_receive(self):
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        self.assertEqual(rma.reception_move_id.picking_id.state, 'assigned')
        self.assertEqual(rma.reception_move_id.product_id, rma.product_id)
        self.assertEqual(rma.reception_move_id.product_uom_qty, 10)
        self.assertEqual(rma.reception_move_id.product_uom, rma.product_uom)
        self.assertEqual(rma.state, 'confirmed')
        self._test_readonly_fields(rma)
        rma.reception_move_id.quantity_done = 9
        with self.assertRaises(ValidationError):
            rma.reception_move_id.picking_id.action_done()
        rma.reception_move_id.quantity_done = 10
        rma.reception_move_id.picking_id.action_done()
        self.assertEqual(rma.reception_move_id.picking_id.state, 'done')
        self.assertEqual(rma.reception_move_id.quantity_done, 10)
        self.assertEqual(rma.state, 'received')
        self._test_readonly_fields(rma)

    def test_cancel(self):
        # cancel a draft RMA
        rma = self._create_rma(self.partner, self.product)
        rma.action_cancel()
        self.assertEqual(rma.state, 'cancelled')
        self._test_readonly_fields(rma)
        # cancel a confirmed RMA
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        rma.action_cancel()
        self.assertEqual(rma.state, 'cancelled')
        # A RMA is only cancelled from draft and confirmed states
        rma = self._create_confirm_receive(self.partner, self.product, 10,
                                           self.rma_loc)
        with self.assertRaises(UserError):
            rma.action_cancel()

    def test_lock_unlock(self):
        # A RMA is only locked from 'received' state
        rma_1 = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma_2 = self._create_confirm_receive(self.partner, self.product, 10,
                                             self.rma_loc)
        self.assertEqual(rma_1.state, 'draft')
        self.assertEqual(rma_2.state, 'received')
        (rma_1 | rma_2).action_lock()
        self.assertEqual(rma_1.state, 'draft')
        self.assertEqual(rma_2.state, 'locked')
        # A RMA is only unlocked from 'lock' state and it will be set
        # to 'received' state
        (rma_1 | rma_2).action_unlock()
        self.assertEqual(rma_1.state, 'draft')
        self.assertEqual(rma_2.state, 'received')

    def test_action_refund(self):
        rma = self._create_confirm_receive(self.partner, self.product, 10,
                                           self.rma_loc)
        self.assertEqual(rma.state, 'received')
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)
        rma.action_refund()
        self.assertEqual(rma.refund_id.type, 'out_refund')
        self.assertEqual(rma.refund_id.state, 'draft')
        self.assertEqual(rma.refund_line_id.product_id, rma.product_id)
        self.assertEqual(rma.refund_line_id.quantity, 10)
        self.assertEqual(rma.refund_line_id.uom_id, rma.product_uom)
        self.assertEqual(rma.state, 'refunded')
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        rma.refund_line_id.quantity = 9
        with self.assertRaises(ValidationError):
            rma.refund_id.action_invoice_open()
        rma.refund_line_id.quantity = 10
        rma.refund_id.action_invoice_open()
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        self._test_readonly_fields(rma)

    def test_mass_refund(self):
        # Create, confirm and receive rma_1
        rma_1 = self._create_confirm_receive(self.partner, self.product, 10,
                                             self.rma_loc)
        # create, confirm and receive 3 more RMAs
        # rma_2: Same partner and same product as rma_1
        rma_2 = self._create_confirm_receive(self.partner, self.product, 15,
                                             self.rma_loc)
        # rma_3: Same partner and different product than rma_1
        product = self.product_product.create(
            {'name': 'Product 2 test', 'type': 'product'})
        rma_3 = self._create_confirm_receive(self.partner, product, 20,
                                             self.rma_loc)
        # rma_4: Different partner and same product as rma_1
        partner = self.res_partner.create({
            'name': 'Partner 2 test',
            'property_account_receivable_id': self.account_receiv.id,
            'company_id': self.company.id,
        })
        rma_4 = self._create_confirm_receive(partner, product, 25,
                                             self.rma_loc)
        # all rmas are ready to refund
        all_rmas = (rma_1 | rma_2 | rma_3 | rma_4)
        self.assertEqual(all_rmas.mapped('state'), ['received']*4)
        self.assertEqual(all_rmas.mapped('can_be_refunded'), [True]*4)
        # Mass refund of those four RMAs
        action = self.env.ref('rma.rma_refund_action_server')
        ctx = dict(self.env.context)
        ctx.update(active_ids=all_rmas.ids, active_model='rma')
        action.with_context(ctx).run()
        # After that all RMAs are in 'refunded' state
        self.assertEqual(all_rmas.mapped('state'), ['refunded'] * 4)
        # Two refunds were created
        refund_1 = (rma_1 | rma_2 | rma_3).mapped('refund_id')
        refund_2 = rma_4.refund_id
        self.assertEqual(len(refund_1), 1)
        self.assertEqual(len(refund_2), 1)
        self.assertEqual((refund_1 | refund_2).mapped('state'), ['draft']*2)
        # One refund per partner
        self.assertNotEqual(refund_1.partner_id, refund_2.partner_id)
        self.assertEqual(
            refund_1.partner_id,
            (rma_1 | rma_2 | rma_3).mapped('partner_invoice_id'),
        )
        self.assertEqual(refund_2.partner_id, rma_4.partner_invoice_id)
        # Each RMA (rma_1, rma_2 and rma_3) is linked with a different
        # line of refund_1
        self.assertEqual(len(refund_1.invoice_line_ids), 3)
        self.assertEqual(
            refund_1.invoice_line_ids.mapped('rma_id'),
            (rma_1 | rma_2 | rma_3),
        )
        self.assertEqual(
            (rma_1 | rma_2 | rma_3).mapped('refund_line_id'),
            refund_1.invoice_line_ids,
        )
        # rma_4 is linked with the unique line of refund_2
        self.assertEqual(len(refund_2.invoice_line_ids), 1)
        self.assertEqual(refund_2.invoice_line_ids.rma_id, rma_4)
        self.assertEqual(rma_4.refund_line_id, refund_2.invoice_line_ids)
        # Assert product and quantities are propagated correctly
        for rma in all_rmas:
            self.assertEqual(rma.product_id, rma.refund_line_id.product_id)
            self.assertEqual(rma.product_uom_qty, rma.refund_line_id.quantity)
            self.assertEqual(rma.product_uom, rma.refund_line_id.uom_id)
        # Less quantity -> error on confirm
        rma_2.refund_line_id.quantity = 14
        with self.assertRaises(ValidationError):
            refund_1.action_invoice_open()
        rma_2.refund_line_id.quantity = 15
        refund_1.action_invoice_open()
        refund_2.action_invoice_open()

    def test_replace(self):
        # Create, confirm and receive an RMA
        rma = self._create_confirm_receive(self.partner, self.product, 10,
                                           self.rma_loc)
        # Replace with another product with quantity 2.
        product_2 = self.product_product.create(
            {'name': 'Product 2 test', 'type': 'product'})
        delivery_form = Form(
            self.env['rma.delivery.wizard'].with_context(
                active_ids=rma.ids,
                rma_delivery_type='replace',
            )
        )
        delivery_form.product_id = product_2
        delivery_form.product_uom_qty = 2
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        self.assertEqual(len(rma.delivery_move_ids.picking_id.move_lines), 1)
        self.assertEqual(rma.delivery_move_ids.product_id, product_2)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 2)
        self.assertTrue(rma.delivery_move_ids.picking_id.state, 'waiting')
        self.assertEqual(rma.state, 'waiting_replacement')
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        first_move = rma.delivery_move_ids
        picking = first_move.picking_id
        # Replace again with another product with the remaining quantity
        product_3 = self.product_product.create(
            {'name': 'Product 3 test', 'type': 'product'})
        delivery_form = Form(
            self.env['rma.delivery.wizard'].with_context(
                active_ids=rma.ids,
                rma_delivery_type='replace',
            )
        )
        delivery_form.product_id = product_3
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        second_move = rma.delivery_move_ids - first_move
        self.assertEqual(len(rma.delivery_move_ids), 2)
        self.assertEqual(rma.delivery_move_ids.mapped('picking_id'), picking)
        self.assertEqual(first_move.product_id, product_2)
        self.assertEqual(first_move.product_uom_qty, 2)
        self.assertEqual(second_move.product_id, product_3)
        self.assertEqual(second_move.product_uom_qty, 8)
        self.assertTrue(picking.state, 'waiting')
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        # remaining_qty is 0 but rma is not set to 'replaced' until
        # remaining_qty_to_done is less than or equal to 0
        first_move.quantity_done = 2
        second_move.quantity_done = 8
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 10)
        self.assertEqual(rma.remaining_qty_to_done, 0)
        # The RMA is now in 'replaced' state
        self.assertEqual(rma.state, 'replaced')
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        # Despite being in 'replaced' state,
        # RMAs can still perform replacements.
        self.assertTrue(rma.can_be_replaced)
        self._test_readonly_fields(rma)

    def test_return_to_customer(self):
        # Create, confirm and receive an RMA
        rma = self._create_confirm_receive(self.partner, self.product, 10,
                                           self.rma_loc)
        # Return the same product with quantity 2 to the customer.
        delivery_form = Form(
            self.env['rma.delivery.wizard'].with_context(
                active_ids=rma.ids,
                rma_delivery_type='return',
            )
        )
        delivery_form.product_uom_qty = 2
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        picking = rma.delivery_move_ids.picking_id
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(rma.delivery_move_ids.product_id, self.product)
        self.assertEqual(rma.delivery_move_ids.product_uom_qty, 2)
        self.assertTrue(picking.state, 'waiting')
        self.assertEqual(rma.state, 'waiting_return')
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_replaced)
        self.assertTrue(rma.can_be_returned)
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 0)
        self.assertEqual(rma.remaining_qty_to_done, 10)
        first_move = rma.delivery_move_ids
        picking = first_move.picking_id
        # Validate the picking
        first_move.quantity_done = 2
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(rma.delivered_qty, 2)
        self.assertEqual(rma.remaining_qty, 8)
        self.assertEqual(rma.delivered_qty_done, 2)
        self.assertEqual(rma.remaining_qty_to_done, 8)
        # Return the remaining quantity to the customer
        delivery_form = Form(
            self.env['rma.delivery.wizard'].with_context(
                active_ids=rma.ids,
                rma_delivery_type='return',
            )
        )
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        second_move = rma.delivery_move_ids - first_move
        second_move.quantity_done = 8
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 2)
        self.assertEqual(rma.remaining_qty_to_done, 8)
        self.assertEqual(rma.state, 'waiting_return')
        # remaining_qty is 0 but rma is not set to 'returned' until
        # remaining_qty_to_done is less than or equal to 0
        picking_2 = second_move.picking_id
        picking_2.button_validate()
        self.assertEqual(picking_2.state, 'done')
        self.assertEqual(rma.delivered_qty, 10)
        self.assertEqual(rma.remaining_qty, 0)
        self.assertEqual(rma.delivered_qty_done, 10)
        self.assertEqual(rma.remaining_qty_to_done, 0)
        # The RMA is now in 'returned' state
        self.assertEqual(rma.state, 'returned')
        self.assertFalse(rma.can_be_refunded)
        self.assertFalse(rma.can_be_returned)
        self.assertFalse(rma.can_be_replaced)
        self._test_readonly_fields(rma)

    def test_mass_return_to_customer(self):
        # Create, confirm and receive rma_1
        rma_1 = self._create_confirm_receive(self.partner, self.product, 10,
                                             self.rma_loc)
        # create, confirm and receive 3 more RMAs
        # rma_2: Same partner and same product as rma_1
        rma_2 = self._create_confirm_receive(self.partner, self.product, 15,
                                             self.rma_loc)
        # rma_3: Same partner and different product than rma_1
        product = self.product_product.create(
            {'name': 'Product 2 test', 'type': 'product'})
        rma_3 = self._create_confirm_receive(self.partner, product, 20,
                                             self.rma_loc)
        # rma_4: Different partner and same product as rma_1
        partner = self.res_partner.create({'name': 'Partner 2 test'})
        rma_4 = self._create_confirm_receive(partner, product, 25,
                                             self.rma_loc)
        # all rmas are ready to be returned to the customer
        all_rmas = (rma_1 | rma_2 | rma_3 | rma_4)
        self.assertEqual(all_rmas.mapped('state'), ['received'] * 4)
        self.assertEqual(all_rmas.mapped('can_be_returned'), [True] * 4)
        # Mass return of those four RMAs
        delivery_wizard = self.env['rma.delivery.wizard'].with_context(
            active_ids=all_rmas.ids, rma_delivery_type='return').create({})
        delivery_wizard.action_deliver()
        # Two pickings were created
        pick_1 = (rma_1 | rma_2 | rma_3).mapped('delivery_move_ids.picking_id')
        pick_2 = rma_4.delivery_move_ids.picking_id
        self.assertEqual(len(pick_1), 1)
        self.assertEqual(len(pick_2), 1)
        self.assertNotEqual(pick_1, pick_2)
        self.assertEqual((pick_1 | pick_2).mapped('state'), ['assigned'] * 2)
        # One picking per partner
        self.assertNotEqual(pick_1.partner_id, pick_2.partner_id)
        self.assertEqual(
            pick_1.partner_id,
            (rma_1 | rma_2 | rma_3).mapped('partner_shipping_id'),
        )
        self.assertEqual(pick_2.partner_id, rma_4.partner_id)
        # Each RMA of (rma_1, rma_2 and rma_3) is linked to a different
        # line of picking_1
        self.assertEqual(len(pick_1.move_lines), 3)
        self.assertEqual(
            pick_1.move_lines.mapped('rma_id'),
            (rma_1 | rma_2 | rma_3),
        )
        self.assertEqual(
            (rma_1 | rma_2 | rma_3).mapped('delivery_move_ids'),
            pick_1.move_lines,
        )
        # rma_4 is linked with the unique move of pick_2
        self.assertEqual(len(pick_2.move_lines), 1)
        self.assertEqual(pick_2.move_lines.rma_id, rma_4)
        self.assertEqual(rma_4.delivery_move_ids, pick_2.move_lines)
        # Assert product and quantities are propagated correctly
        for rma in all_rmas:
            self.assertEqual(rma.product_id, rma.delivery_move_ids.product_id)
            self.assertEqual(rma.product_uom_qty,
                             rma.delivery_move_ids.product_uom_qty)
            self.assertEqual(rma.product_uom,
                             rma.delivery_move_ids.product_uom)
            rma.delivery_move_ids.quantity_done = rma.product_uom_qty
        pick_1.button_validate()
        pick_2.button_validate()
        self.assertEqual(all_rmas.mapped('state'), ['returned'] * 4)

    def test_rma_from_picking_return(self):
        # Create a return from a delivery picking
        origin_delivery = self._create_delivery()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_id=origin_delivery.id,
            active_ids=origin_delivery.ids,
        ).create({'create_rma': True})
        picking_action = return_wizard.create_returns()
        # Each origin move is linked to a different RMA
        origin_moves = origin_delivery.move_lines
        self.assertTrue(origin_moves[0].rma_ids)
        self.assertTrue(origin_moves[1].rma_ids)
        rmas = origin_moves.mapped('rma_ids')
        self.assertEqual(rmas.mapped('state'), ['confirmed']*2)
        # Each reception move is linked one of the generated RMAs
        reception = self.env['stock.picking'].browse(picking_action['res_id'])
        reception_moves = reception.move_lines
        self.assertTrue(reception_moves[0].rma_receiver_ids)
        self.assertTrue(reception_moves[1].rma_receiver_ids)
        self.assertEqual(reception_moves.mapped('rma_receiver_ids'), rmas)
        # Validate the reception picking to set rmas to 'received' state
        reception_moves[0].quantity_done = reception_moves[0].product_uom_qty
        reception_moves[1].quantity_done = reception_moves[1].product_uom_qty
        reception.button_validate()
        self.assertEqual(rmas.mapped('state'), ['received'] * 2)

    def test_split(self):
        origin_delivery = self._create_delivery()
        rma_form = Form(self.env['rma'])
        rma_form.partner_id = self.partner
        rma_form.picking_id = origin_delivery
        rma_form.move_id = origin_delivery.move_lines.filtered(
            lambda r: r.product_id == self.product)
        rma = rma_form.save()
        rma.action_confirm()
        rma.reception_move_id.quantity_done = 10
        rma.reception_move_id.picking_id.action_done()
        # Return quantity 4 of the same product to the customer
        delivery_form = Form(
            self.env['rma.delivery.wizard'].with_context(
                active_ids=rma.ids,
                rma_delivery_type='return',
            )
        )
        delivery_form.product_uom_qty = 4
        delivery_wizard = delivery_form.save()
        delivery_wizard.action_deliver()
        rma.delivery_move_ids.quantity_done = 4
        rma.delivery_move_ids.picking_id.button_validate()
        self.assertEqual(rma.state, 'waiting_return')
        # Extract the remaining quantity to another RMA
        self.assertTrue(rma.can_be_split)
        split_wizard = self.env['rma.split.wizard'].with_context(
            active_id=rma.id,
            active_ids=rma.ids,
        ).create({})
        action = split_wizard.action_split()
        # Check rma is set to 'returned' after split. Check new_rma values
        self.assertEqual(rma.state, 'returned')
        new_rma = self.env['rma'].browse(action['res_id'])
        self.assertEqual(new_rma.origin_split_rma_id, rma)
        self.assertEqual(new_rma.delivered_qty, 0)
        self.assertEqual(new_rma.remaining_qty, 6)
        self.assertEqual(new_rma.delivered_qty_done, 0)
        self.assertEqual(new_rma.remaining_qty_to_done, 6)
        self.assertEqual(new_rma.state, 'received')
        self.assertTrue(new_rma.can_be_refunded)
        self.assertTrue(new_rma.can_be_returned)
        self.assertTrue(new_rma.can_be_replaced)
        self.assertEqual(new_rma.move_id, rma.move_id)
        self.assertEqual(new_rma.reception_move_id, rma.reception_move_id)
        self.assertEqual(new_rma.product_uom_qty + rma.product_uom_qty, 10)
        self.assertEqual(new_rma.move_id.quantity_done, 10)
        self.assertEqual(new_rma.reception_move_id.quantity_done, 10)

    def test_rma_to_receive_on_delete_invoice(self):
        rma = self._create_confirm_receive(self.partner, self.product, 10,
                                           self.rma_loc)
        rma.action_refund()
        self.assertEqual(rma.state, 'refunded')
        rma.refund_id.unlink()
        self.assertFalse(rma.refund_id)
        self.assertEqual(rma.state, 'received')
        self.assertTrue(rma.can_be_refunded)
        self.assertTrue(rma.can_be_returned)
        self.assertTrue(rma.can_be_replaced)

    def test_rma_picking_type_default_values(self):
        warehouse = self.env['stock.warehouse'].create({
            'name': 'Stock - RMA Test',
            'code': 'SRT',
        })
        self.assertFalse(warehouse.rma_in_type_id.use_create_lots)
        self.assertTrue(warehouse.rma_in_type_id.use_existing_lots)

    def test_quantities_on_hand(self):
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.action_confirm()
        rma.reception_move_id.quantity_done = 10
        rma.reception_move_id.picking_id.action_done()
        self.assertEqual(rma.product_id.qty_available, 0)

    def test_autoconfirm_email(self):
        rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma.company_id.send_rma_confirmation = True
        rma.company_id.rma_mail_confirmation_template_id = (
            self.env.ref("rma.mail_template_rma_notification")
        )
        previous_mails = self.env["mail.mail"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        self.assertFalse(previous_mails)
        rma.action_confirm()
        mail = self.env["mail.message"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        self.assertTrue(rma.name in mail.subject)
        self.assertTrue(rma.name in mail.body)
