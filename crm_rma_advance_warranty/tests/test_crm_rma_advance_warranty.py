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
from openerp.tests.common import TransactionCase


class TestCrmRmaAdvanceWarranty(TransactionCase):

    def setUp(self):
        super(TestCrmRmaAdvanceWarranty, self).setUp()
        self.claim = self.env['crm.claim']
        self.claim_line = self.env['claim.line']
        res_partner = self.env['res.partner']
        self.sale_order = self.env['sale.order']

        self.claim_type = self.ref('crm_claim_type.crm_claim_type_customer')
        self.supplier_id = res_partner.browse(self.ref('base.res_partner_1'))

    def get_customer_sale_order_and_invoice(self, set_supplier=False):
        sale_order_id = self.sale_order.browse(
            self.ref('sale.sale_order_7'))[0].copy()
        # remove first order line just to simplify things up
        sale_order_id.write({
            'order_line': [(3, sale_order_id.order_line[0].id)]
        })

        if set_supplier:
            sale_order_id.write({
                'order_line': [(1, sale_order_id.order_line[0].id, {
                    'supplier_id': self.supplier_id.id
                }), (1, sale_order_id.order_line[1].id, {
                    'supplier_id': self.supplier_id.id
                }), (1, sale_order_id.order_line[2].id, {
                    'supplier_id': self.supplier_id.id
                }), ]
            })

        sale_order_id.action_button_confirm()
        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)

        invoice_id = sale_order_id.invoice_ids[0]
        invoice_id.signal_workflow('invoice_open')
        return invoice_id

    def create_customer_claim(self, invoice_id):
        """
        Create a customer claim with or without claim lines based
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
        return claim_id

    def test_01_warranty_company_limit(self):
        invoice_id = self.get_customer_sale_order_and_invoice()
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
