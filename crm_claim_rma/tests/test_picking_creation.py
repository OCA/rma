# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#            Yanina Aular
#    Copyright 2015 Vauxoo
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tests import common


class TestPickingCreation(common.TransactionCase):

    """ Test the correct pickings are created by the wizard. """

    def setUp(self):
        super(TestPickingCreation, self).setUp()

        self.wizard_make_picking = self.env['claim_make_picking.wizard']
        self.stockpicking = self.env['stock.picking']
        claim = self.env['crm.claim']

        self.product_id = self.env.ref('product.product_product_4')

        self.partner_id = self.env.ref('base.res_partner_12')

        self.customer_location_id = self.env.ref(
            'stock.stock_location_customers')

        sale_order_agrolait_demo = self.env.ref('sale.sale_order_1')
        self.assertTrue(sale_order_agrolait_demo.invoice_ids,
                        "The Order Sale of Agrolait not have Invoice")
        invoice_agrolait = sale_order_agrolait_demo.invoice_ids[0]
        invoice_agrolait.\
            signal_workflow('invoice_open')

        # Create the claim with a claim line
        self.claim_id = claim.create(
            {
                'name': 'TEST CLAIM',
                'code': '/',
                'claim_type': self.env.ref('crm_claim_type.'
                                           'crm_claim_type_customer').id,
                'delivery_address_id': self.partner_id.id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'invoice_id': invoice_agrolait.id,
            })
        self.claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()
        self.warehouse_id = self.claim_id.warehouse_id

    def test_00_new_product_return(self):
        """Test wizard creates a correct picking for product return

        """
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'in',
            'product_return': True,
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]
        self.assertEquals(picking.location_id, self.customer_location_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id,
                          self.warehouse_id.lot_stock_id,
                          "Incorrect destination location")

    def test_01_new_delivery(self):
        """Test wizard creates a correct picking for a new delivery

        """

        wizardchangeproductqty = self.env['stock.change.product.qty']
        wizard_chg_qty = wizardchangeproductqty.with_context({
            'active_id': self.product_id.id,
        }).create({
            'product_id': self.product_id.id,
            'new_quantity': 12,
        })

        wizard_chg_qty.change_product_qty()

        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'out',
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]

        self.assertEquals(picking.location_id, self.warehouse_id.lot_stock_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id, self.customer_location_id,
                          "Incorrect destination location")

    def test_02_new_product_return(self):
        """Test wizard creates a correct picking for product return

        """
        company = self.env.ref('base.main_company')
        warehouse_obj = self.env['stock.warehouse']
        warehouse_rec = \
            warehouse_obj.search([('company_id',
                                   '=', company.id)])[0]
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': warehouse_rec.in_type_id.id,
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]

        self.assertEquals(picking.location_id, self.customer_location_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id,
                          self.warehouse_id.lot_stock_id,
                          "Incorrect destination location")

    def create_invoice(self):
        sale_order_id = self.env['sale.order'].create({
            'partner_id': self.ref('base.res_partner_9'),
            'client_order_ref': 'TEST_SO',
            'order_policy': 'manual',
            'order_line': [(0, 0, {
                'product_id': self.ref('product.product_product_8'),
                'product_uom_qty': 2
            })]
        })
        sale_order_id.action_button_confirm()
        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)
        invoice_id = sale_order_id.invoice_ids
        invoice_id.signal_workflow('invoice_open')
        return invoice_id

    def test_03_invoice_refund(self):
        claim_id = self.env['crm.claim'].browse(
            self.ref('crm_claim.crm_claim_6'))
        invoice_id = self.env['account.invoice'].browse(
            self.ref('account.invoice_5'))
        claim_id.write({
            'invoice_id': invoice_id.id
        })
        claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()

        invoice_refund_wizard_id = self.env['account.invoice.refund'].\
            with_context({
                'active_ids': [claim_id.invoice_id.id],
                'claim_line_ids':
                [[4, cl.id, False] for cl in claim_id.claim_line_ids],
            }).create({
                'description': "Testing Invoice Refund for Claim"
            })

        res = invoice_refund_wizard_id.invoice_refund()

        self.assertTrue(res)
        self.assertEquals(res['res_model'], 'account.invoice')
        self.assertEquals(eval(res['context'])['type'], 'out_refund')

    def test_04_display_name(self):
        """
        It tests that display_name for each line has a message for it
        """
        claim_line_ids = self.env['crm.claim'].browse(
            self.ref('crm_claim.crm_claim_6'))[0].claim_line_ids

        all_values = sum([bool(line_id.display_name)
                          for line_id in claim_line_ids])
        self.assertEquals(len(claim_line_ids), all_values)
