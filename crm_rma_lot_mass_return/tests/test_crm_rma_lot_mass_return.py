# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Osval Reyes
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
from datetime import date


class TestCrmRmaLotMassReturn(TransactionCase):

    """
    Test cases for CRM RMA Lot Mass Return Module
    """

    def setUp(self):
        super(TestCrmRmaLotMassReturn, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.sale_order_id = self.create_sale_order()
        self.invoice_id = self.sale_order_id.invoice_ids[0]
        self.claim_id = self.env['crm.claim'].\
            create({
                'name': 'Test',
                'claim_type': self.ref('crm_claim_type.'
                                       'crm_claim_type_customer'),
                'partner_id': self.invoice_id.partner_id.id,
                'pick': True
            })

    def create_sale_order(self):
        self.sale_order_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'note': 'Sale Order Test',
            'order_policy': 'prepaid',
            'payment_term': self.ref('account.account_payment_term'),
            'order_line': [(0, 0, {
                    'name': 'Test',
                    'product_id': self.ref('product.product_product_8'),
                    'product_uom_qty': 16
            })]
        })

        self.sale_order_id.action_button_confirm()

        return self.sale_order_id

    def test_01_render_metasearch_view(self):
        res = self.claim_id.render_metasearch_view()
        self.assertEqual(res['res_model'], self.metasearch_wizard._name)

    def test_02_load_products(self):
        self.invoice_id.signal_workflow('invoice_open')

        # Before continue, invoice must be open to get a number value
        # and this is needed by the wizard
        self.assertEqual(self.invoice_id.state, 'open')

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            self.invoice_id.number, [(0, 6, [])])['value']['lines_id'][0][2]

        wizard_id.lines_list_id = lines_list_id

        # it exists at least one line
        self.assertNotEqual(len(lines_list_id), 0)

        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id),
                         len(self.invoice_id.invoice_line.ids))

        wizard_id.change_list(lines_list_id)
        wizard_id.scan_data = self.invoice_id.number + '\n'
        wizard_id.add_claim_lines()

        # Claim record it must have same line count as the invoice
        self.assertEqual(len(self.claim_id.claim_line_ids),
                         len(self.invoice_id.invoice_line))
