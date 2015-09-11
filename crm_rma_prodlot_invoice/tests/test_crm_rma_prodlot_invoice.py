# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular, Osval Reyes
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


class TestCrmRmaProdLotInvoice(TransactionCase):

    """
    Test Cases
    """

    def setUp(self):
        super(TestCrmRmaProdLotInvoice, self).setUp()
        self.so_obj = self.env['sale.order']
        self.sol_obj = self.env['sale.order.line']
        self.inv_obj = self.env['account.invoice']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.av_obj = self.env['account.voucher']
        self.cash_type_journal_id = self.env['account.journal'].\
            search([('type', '=', 'cash')], limit=1)[0]
        self.product_id = self.ref(
            'product.product_product_8_product_template')

    def test_01_action_ship_create(self):
        """
        Create sale order with Before Delivery policy
        """
        sale_order = self.so_obj.create({
            'partner_id': self.partner_id.id,
            'client_order_ref': 'TEST_SO',
            'order_policy': 'prepaid',  # 'before delivery' invoice creation
            'order_line': [(0, 0, {
                'product_id': self.product_id,
            })]
        })

        sale_order.action_button_confirm()
        for invoice_id in sale_order.invoice_ids:
            invoice_id.invoice_validate()

            # check
            self.assertEqual(invoice_id.state, 'open')

            invoice_id.invoice_pay_customer()
            payment_id = self.av_obj.create({
                'partner_id': self.partner_id.id,
                'amount': invoice_id.amount_total,
                'journal_id': self.cash_type_journal_id.id,
                'payment_option': 'without_writeoff',
                'reference': 'TEST_INVOICE',
                'name': 'Invoice' + sale_order.client_order_ref,
                'account_id': invoice_id.account_id.id
            })

            inv_lines = self.env['account.invoice.line'].\
                search([('invoice_id', '=', invoice_id.id)])

            self.assertNotEqual(len(inv_lines), 0)

            payment_id.button_proforma_voucher()

            failed_olines = [inv_line
                             for inv_line in invoice_id.invoice_line
                             if inv_line.move_id is False]
            self.assertEqual(failed_olines, [])
