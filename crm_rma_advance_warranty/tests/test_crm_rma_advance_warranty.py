# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Osval Reyes,
#            Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later versionself.
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
from datetime import date
from openerp.tests.common import TransactionCase
from openerp.exceptions import Warning as UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestCrmRmaAdvanceWarranty(TransactionCase):

    def setUp(self):
        super(TestCrmRmaAdvanceWarranty, self).setUp()
        self.claim = self.env['crm.claim']
        self.claim_line = self.env['claim.line']
        self.sale_order = self.env['sale.order']
        self.purchase_order = self.env['purchase.order']
        self.claim_type = self.ref('crm_claim_rma.crm_claim_type_customer')
        self.supplier_id = self.env.ref('base.res_partner_6')
        self.customer_id = self.env.ref('base.res_partner_23')
        self.product_id = self.env.ref('product.product_product_8')

    def do_picking(self, picking_ids):
        wizard = self.env['stock.transfer_details']
        wizard_item = self.env['stock.transfer_details_items']
        stock_location_id = self.env.ref('stock.stock_location_stock')

        lot_ids = []
        for picking_id in picking_ids:
            picking_id.write({"invoice_state": "2binvoiced"})
            wizard_id = wizard.create({
                'picking_id': picking_id.id
            })
            for move_id in picking_id.move_lines.mapped('id'):
                move_id = self.env['stock.move'].browse(move_id)
                move_id.write({"invoice_state": "2binvoiced"})
                lot_id = self.env['stock.production.lot'].create({
                    'name': 'lot-' + str(move_id.id),
                    'product_id': move_id.product_id.id,
                })
                lot_ids.append(lot_id.id)
                wizard_item.create({
                    'transfer_id': wizard_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': 1,
                    'sourceloc_id': move_id.location_id.id,
                    'destinationloc_id': stock_location_id.id,
                    'lot_id': lot_id.id,
                    'product_uom_id': move_id.product_uom.id,
                })
            wizard_id.do_detailed_transfer()

        return self.env['stock.production.lot'].browse(lot_ids)

    def create_purchase_order(self, supplier_id, product_id):
        purchase_order_id = self.purchase_order.create({
            'partner_id': supplier_id.id,
            'location_id': self.ref('stock.picking_type_in'),
            'pricelist_id': 1,
            'order_line': [(0, 0, {
                'name': 'Test',
                'product_id': product_id.id,
                'price_unit': product_id.list_price,
                'product_qty': 1,
                'date_planned': date.today().replace(day=31, month=12).
                strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })]
        })

        purchase_order_id.wkf_confirm_order()
        purchase_order_id.action_invoice_create()
        purchase_order_id.action_picking_create()
        self.assertEquals(purchase_order_id.state, 'confirmed')
        self.picking_ids = purchase_order_id.picking_ids
        return purchase_order_id

    def create_sale_order_and_invoice(self, partner_id, invoicing_rule,
                                      product_id):
        sale_order_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'client_order_ref': 'Test',
            'order_policy': invoicing_rule,
            'order_line': [(0, 0, {
                'product_id': product_id.id,
                'product_uom_qty': 1
            })]
        })
        sale_order_id.action_button_confirm()
        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)

        return sale_order_id.invoice_ids[0]

    def create_customer_claim(self, invoice_id):
        """Create a customer claim with or without claim lines based
        on include_lines parameter
        """
        customer_id = invoice_id.partner_id
        claim_id = self.claim.create({
            'name': 'Test Claim for %s' % (customer_id.name),
            'claim_type': self.claim_type,
            'partner_id': customer_id.id,
            'pick': True,
            'code': '/',
            'invoice_id': invoice_id.id,
        })
        claim_id.with_context(
            {'create_lines': True})._onchange_invoice_warehouse_type_date()
        claim_id.claim_line_ids.write({
            'supplier_id': self.supplier_id.id,
        })
        return claim_id

    def test_01_warranty_company_limit(self):
        invoice_id = self.create_sale_order_and_invoice(
            self.customer_id, 'prepaid', self.product_id)
        invoice_id.signal_workflow('invoice_open')
        claim_id = self.create_customer_claim(invoice_id)

        # check if it has the same line count
        self.assertEquals(len(invoice_id.invoice_line),
                          len(claim_id.claim_line_ids))

        claim_id.claim_line_ids.set_warranty()

        # check if warranty set is company for all of them
        wtypes = claim_id.mapped('claim_line_ids.warranty_type')

        self.assertFalse([w for w in wtypes if w != 'company'])

        for line_id in claim_id.claim_line_ids:
            # warranty return address values

            self.assertTrue(line_id.warranty_return_partner and
                            line_id.warranty_type and
                            line_id.location_dest_id)
            # warranty limit values
            self.assertTrue(line_id.guarantee_limit and
                            line_id.set_warranty_limit)

    def test_02_invoice_without_date(self):
        """Invoices used for claim lines requires to be open (validated)
        in order to compute warranty based on its invoice date and also
        the warranty limits based on supplier registered within the serial/lot,
        in counter case an error will be thrown
        """
        invoice_id = self.create_sale_order_and_invoice(
            self.customer_id, 'prepaid', self.product_id)
        claim_id = self.create_customer_claim(invoice_id)
        self.assertEqual(invoice_id.state, 'draft')

        # Expect an exception based on draft invoice
        error_msg = '.*Cannot find any date for invoice.*'
        with self.assertRaisesRegexp(UserError, error_msg):
            claim_id.claim_line_ids.set_warranty()

        # Validate invoice
        invoice_id.signal_workflow('invoice_open')

        # Set serial/lot for every claim line and also a 'supplier warranty'
        for line_id in claim_id.claim_line_ids:
            lot_id = self.env['stock.production.lot'].create({
                'product_id': line_id.product_id.id,
                'name': line_id.name,
            })
            line_id.write({
                'warranty_type': 'supplier',
                'prodlot_id': lot_id.id
            })
        error_msg = '.*The product has no supplier configured.*'
        with self.assertRaisesRegexp(UserError, error_msg):
            claim_id.claim_line_ids.set_warranty()

    def write_product_supplier(self, product_id, supplier_id, duration=0,
                               rewrite=True):
        """Write or rewrite supplier info if needed
        """
        seller_id = product_id.seller_ids.filtered(
            lambda r: r.name == supplier_id)
        if rewrite and seller_id:
            seller_id.write({'warranty_duration': duration})
        else:
            seller_dict = {
                'name': supplier_id.id,
                'active_supplier': True,
                'warranty_duration': duration,
                'product_tmpl_id': product_id.product_tmpl_id.id,
            }
            product_id.write({
                'seller_ids': [(0, 0, seller_dict)]
            })

    def test_03_more_than_one_active_supplier(self):
        """When one product have more than one record for its suppliers, an
        error should be raised
        """
        invoice_id = self.create_sale_order_and_invoice(
            self.customer_id, 'prepaid', self.product_id)
        line_id = self.create_customer_claim(invoice_id).claim_line_ids[0]

        # write (yes, twice) a supplier for product as seller
        self.write_product_supplier(line_id.product_id, line_id.supplier_id,
                                    rewrite=False)
        self.write_product_supplier(line_id.product_id, line_id.supplier_id,
                                    rewrite=False)

        # verify that error raised
        error_msg = '.*There are more than one supplier activated.*'
        with self.assertRaisesRegexp(UserError, error_msg):
            line_id._get_product_supplier_info()

    def test_04_warranty_calculation(self):
        """Set warranty valid based on days in product's supplier warranty
        """
        # purchase a product
        purchase_order_id = self.create_purchase_order(self.supplier_id,
                                                       self.product_id)
        lot_ids = self.do_picking(purchase_order_id.picking_ids)
        self.assertEqual(len(lot_ids), 1)
        lot_id = lot_ids[0]

        # relate product with current supplier
        self.write_product_supplier(self.product_id, self.supplier_id, 0)

        # sell the same product to a customer
        invoice_id = self.create_sale_order_and_invoice(
            self.customer_id, 'prepaid', self.product_id)
        invoice_id.signal_workflow('invoice_open')

        # create a customer claim
        line_id = self.create_customer_claim(invoice_id).claim_line_ids[0]
        line_id.set_warranty()

        # validate is warranty is expired
        self.assertEqual(line_id.warning, 'not_define')

        self.write_product_supplier(self.product_id, self.supplier_id, 1)
        line_id.write({
            'warranty_type': 'supplier',
            'prodlot_id': lot_id.id,
        })
        line_id.set_warranty()

        self.assertEqual(line_id.warning, 'valid')

    def test_05_warranty_calculation(self):
        """Set warranty valid based on days in product's warranty
        """
        invoice_id = self.create_sale_order_and_invoice(
            self.customer_id, 'prepaid', self.product_id)
        invoice_id.signal_workflow('invoice_open')
        line_id = self.create_customer_claim(invoice_id).claim_line_ids[0]
        self.write_product_supplier(line_id.product_id, line_id.supplier_id, 0)

        # validate is warranty is not defined
        line_id.set_warranty()
        self.assertEqual(line_id.warning, 'not_define')

        # set new product warranty limit (company owns the warranty)
        line_id.product_id.write({
            'warranty': 1000,
        })
        line_id.set_warranty()

        # now the warranty is valid based on days set
        self.assertEqual(line_id.warning, 'valid')
