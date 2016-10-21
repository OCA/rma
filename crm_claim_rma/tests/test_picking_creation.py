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
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning as UserError
from .common import ClaimTestsCommon


class TestPickingCreation(ClaimTestsCommon):
    """Test the correct pickings are created by the wizard. """

    def setUp(self):
        super(TestPickingCreation, self).setUp()

        self.wizard_make_picking = self.env['claim_make_picking.wizard']
        self.stockpicking = self.env['stock.picking']
        self.claim = self.env['crm.claim']

        self.product_id = self.env.ref('product.product_product_4')

        self.customer_location_id = self.env.ref(
            'stock.stock_location_customers')

        sale_id = self.create_sale_order(self.rma_customer_id)
        sale_id.signal_workflow('manual_invoice')
        self.assertTrue(sale_id.invoice_ids,
                        "The Order Sale of Agrolait not have Invoice")
        invoice_id = sale_id.invoice_ids[0]
        invoice_id.signal_workflow("invoice_open")

        main_warehouse = self.env.ref("stock.warehouse0")
        sales_team = self.env.ref('sales_team.section_sales_department')
        sales_team.write({"default_warehouse": main_warehouse.id})
        self.env.user.write({'default_section_id': sales_team.id})

        # Create the claim with a claim line
        self.claim_id = self.create_claim(self.customer_type,
                                          self.rma_customer_id,
                                          address_id=self.rma_customer_id,
                                          invoice_id=invoice_id,
                                          name='Claim for Picking Creation')

        self.claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()
        self.warehouse_id = self.claim_id.warehouse_id

    def test_00_new_product_return(self):
        """Test wizard creates a correct picking for product return
        """
        wizard = self.wizard_make_picking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.rma_customer_id.id,
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
                          self.warehouse_id.lot_rma_id,
                          "Incorrect destination location")
        wizard.action_cancel()

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
            'partner_id': self.rma_customer_id.id,
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
            'partner_id': self.rma_customer_id.id,
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

    def test_03_invoice_refund(self):
        claim_id = self.env.ref('crm_claim.crm_claim_6')
        invoice_id = self.env.ref('account.invoice_5')
        claim_id.write({
            'invoice_id': invoice_id.id
        })
        claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()

        refund_id = self.env['account.invoice.refund'].\
            with_context({
                'active_ids': [claim_id.invoice_id.id],
                'claim_line_ids':
                [[4, cl.id, False] for cl in claim_id.claim_line_ids],
                'description': "Testing Invoice Refund for Claim"
            }).create({})

        res = refund_id.invoice_refund()
        self.assertEqual(refund_id.description,
                         refund_id._default_description())
        self.assertTrue(res)
        self.assertEquals(res['res_model'], 'account.invoice')
        self.assertEquals(safe_eval(res['context'])['type'], 'out_refund')

        # Try refunding again, an exception is expected to be raised
        error_msg = 'A refund has already been created for this claim !'
        with self.assertRaisesRegexp(UserError, error_msg):
            refund_id.invoice_refund()

    def test_04_display_name(self):
        """It tests that display_name for each line has a message for it
        """
        claim_line_ids = self.env['crm.claim'].browse(
            self.ref('crm_claim.crm_claim_6'))[0].claim_line_ids

        all_values = sum([bool(line_id.display_name)
                          for line_id in claim_line_ids])
        self.assertEquals(len(claim_line_ids), all_values)

    def test_05_validate_return_value(self):
        """Check computed field got the expected values
        """
        claim_id = self.env.ref('crm_claim.crm_claim_6')
        expected_vals = [cl.unit_sale_price * cl.product_returned_quantity
                         for cl in claim_id.claim_line_ids]
        resulting_vals = claim_id.claim_line_ids.mapped('return_value')
        self.assertEqual(resulting_vals, expected_vals, "Returned values for "
                         "claim lines aren't the correct ones")

    def test_06_invoice_without_date(self):
        """Validate that invoice has date, for warranty purposes
        """

        claim_id = self.env.ref('crm_claim.crm_claim_6')
        line_id = claim_id.claim_line_ids[0]
        sale_order_id = self.env['sale.order'].create({
            'partner_id': self.rma_customer_id.id,
            'client_order_ref': 'TEST_SO',
            'order_policy': 'manual',
            'order_line': [(0, 0, {
                'product_id': self.ref('product.product_product_8'),
                'product_uom_qty': 2
            })]
        })
        sale_order_id.action_button_confirm()
        sale_order_id.action_invoice_create()
        invoice_id = sale_order_id.invoice_ids[0]
        error_msg = 'Cannot find any date for invoice. Must be validated.'
        with self.assertRaisesRegexp(UserError, error_msg):
            line_id._get_warranty_limit_values(
                invoice_id, claim_id.claim_type, line_id.product_id,
                claim_id.date)
        invoice_id.signal_workflow('invoice_open')
        res = line_id._get_warranty_limit_values(
            invoice_id, claim_id.claim_type, line_id.product_id, claim_id.date)
        self.assertTrue(res.get('guarantee_limit', False) and
                        res.get('warning', False))

    def test_07_without_invoice_date(self):
        """Warranty limit and Warning must be set to false from claim
        document if invoice date if not set
        """
        invoice_id = self.env.ref('crm_claim_rma.crm_rma_invoice_003')
        invoice_id.write({'date_invoice': False})
        claim_id = self.create_claim(self.customer_type,
                                     invoice_id.partner_id,
                                     invoice_id=invoice_id,
                                     name='Claim for Picking Creation #2')
        claim_id.with_context({'create_lines': True}).\
            _onchange_invoice_warehouse_type_date()

        lines_guarantees = claim_id.claim_line_ids.mapped('guarantee_limit')
        lines_warnings = claim_id.claim_line_ids.mapped('warning')

        self.assertFalse(any(lines_guarantees) or any(lines_warnings),
                         'All lines should have guarantee_limit and warning '
                         'set to false')

    def test_08_product_return_with_multiple_adresses(self):
        """Validate that a claim with multiple addresses in their lines
        cannot be made
        """
        sale_id = self.sale_order
        customer_type = self.env.ref('crm_claim_rma.crm_claim_type_customer')

        claim_id = self.env['crm.claim'].create({
            'name': 'Claim Product Return',
            'code': '/',
            'claim_type': customer_type.id,
            'partner_id': sale_id.partner_id.id,
            'pick': True,
            'claim_line_ids': [(0, 0, {
                'name': 'test 1',
                'claim_origin': 'damaged',
                'product_id': sale_id.order_line[0].product_id.id,
                'invoice_line_id': sale_id.order_line[0].invoice_lines[0].id,
            }), (0, 0, {
                'name': 'test 2',
                'claim_origin': 'damaged',
                'product_id': sale_id.order_line[1].product_id.id,
                'invoice_line_id': sale_id.order_line[1].invoice_lines[0].id,
            })],
        })
        line_ids = claim_id.claim_line_ids
        claim_id.write({'stage_id': self.ref('crm_claim.stage_claim5')})

        # Write different stock locations for claim lines in order to trigger
        # and exception when trying to create the picking
        multiple_locations = [{
            'location_dest_id': self.ref('stock.stock_location_stock'),
            'warranty_return_partner': self.ref('base.res_partner_address_1'),
        }, {
            'location_dest_id': self.ref('stock.stock_location_shop0'),
            'warranty_return_partner': self.ref('base.res_partner_address_1'),
        }]
        for line_id, record in zip(line_ids, multiple_locations):
            line_id.write(record)

        wizard_id = self.wizard_make_picking.with_context({
            'active_id': claim_id.id,
            'partner_id': claim_id.partner_id.id,
            'warehouse_id': claim_id.warehouse_id.id,
            'picking_type': 'in',
            'product_return': True,
        }).create({})
        error_msg = '.*return cannot be created.*various.*locations.*'
        with self.assertRaisesRegexp(UserError, error_msg):
            wizard_id.action_create_picking()

        # Write different addresses for claim lines in order to trigger
        # and exception when trying to create the picking
        multiple_partners = [{
            'location_dest_id': self.ref('stock.stock_location_stock'),
            'warranty_return_partner': self.ref('base.res_partner_address_1'),
        }, {
            'location_dest_id': self.ref('stock.stock_location_stock'),
            'warranty_return_partner': self.ref('base.res_partner_address_3'),
        }]

        for line_id, record in zip(line_ids, multiple_partners):
            line_id.write(record)
        error_msg = '.*return cannot be created.*various.*addresses.*'

        # before try to create picking the supplier of one of the product must
        # be changed in order to have multiple return addresses that is
        # set when the warranty is calculated for each claim line
        line_ids[1].product_id.seller_ids.write({
            'warranty_return_partner': 'supplier',
        })
        with self.assertRaisesRegexp(UserError, error_msg):
            wizard_id.action_create_picking()
