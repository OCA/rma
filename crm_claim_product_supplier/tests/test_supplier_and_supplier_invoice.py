# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
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

from openerp.tests.common import TransactionCase


class TestSupplierAndSupplierInvoice(TransactionCase):

    def setUp(self):
        super(TestSupplierAndSupplierInvoice, self).setUp()

        self.customer_id = self.env['res.partner'].create({
            'name': 'Larry Ellison',
            'company_id': self.ref('base.main_company'),
            'customer': True,
            'email': 'lellison@yourcompany.example.com',
            'phone': '+8860241622023',
            'street': 'East Western Avenue',
            'city': 'Florida',
            'zip': 51012,
            'country_id': self.ref('base.us'),
            # dear future me: the following field doesn't exist yet,
            # but it does when running from client repository
            'credit_limit': 100000000,
        })
        # Validate last purchase invoice
        self.purchase = self.env.ref(
            "crm_claim_product_supplier.purchase_order_supplier_1")
        self.purchase.invoice_ids.signal_workflow("invoice_open")

        # Create sale.order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'client_order_ref': 'TEST_SO_1',
            'order_policy': 'manual',
            'order_line': [(0, 0, {
                'product_id': self.ref('product.product_product_8'),
                'product_uom_qty': 2,
            })]
        })
        sale_order.action_button_confirm()
        sale_order.action_invoice_create()
        self.assertTrue(sale_order.invoice_ids)
        invoice = sale_order.invoice_ids
        invoice.signal_workflow('invoice_open')

        # Make transfer of product in sale.order
        transfer_obj = self.env["stock.transfer_details"]

        picking = sale_order.picking_ids[0]
        picking.action_assign()
        ctx = {"active_id": picking.id,
               "active_ids": [picking.id],
               "active_model": "stock.picking"}

        wizard_transfer_id = transfer_obj.\
            with_context(ctx).create({"picking_id": picking.id})
        wizard_transfer_id.do_detailed_transfer()

        # Create claim

        self.claim = self.env['crm.claim'].\
            create({
                'name': 'TEST CLAIM',
                'claim_type': self.ref('crm_claim_rma.'
                                       'crm_claim_type_customer'),
                'partner_id': self.customer_id.id,
                'pick': True,
                'user_id': self.env.user.id,
                'company_id': self.env.user.company_id.id,
            })

        # Add claim line

        metasearch_wizard = self.env['returned.lines.from.serial.wizard']

        wizard_id = metasearch_wizard.with_context({
            'active_model': "crm.claim",
            'active_id': self.claim.id,
            'active_ids': [self.claim.id]
        }).create({})

        scan_data = invoice.number + "\n"
        info_wizard = wizard_id.onchange_load_products(
            scan_data,
            [(6, 0, [])])

        lines_list_id = info_wizard['domain']['lines_list_id'][0][2]
        wizard_id.lines_list_id = lines_list_id

        self.assertEqual(len(lines_list_id), 2)
        wizard_id.add_claim_lines()

    def test_check_supplier_and_supplier_invoice(self):

        supplier = self.env.ref("base.res_partner_16")
        self.assertEquals(self.claim.claim_line_ids[0].supplier_id,
                          supplier)
        self.assertEquals(self.claim.claim_line_ids[0].supplier_invoice_id,
                          self.purchase.invoice_ids[0])

        self.assertEquals(self.claim.claim_line_ids[1].supplier_id,
                          supplier)
        self.assertEquals(self.claim.claim_line_ids[1].supplier_invoice_id,
                          self.purchase.invoice_ids[0])
