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
from datetime import date


class TestCrmRmaProdLotInvoice(TransactionCase):

    """
    Test Cases
    """

    def setUp(self):
        super(TestCrmRmaProdLotInvoice, self).setUp()
        self.sale_order = self.env['sale.order']
        self.invoice_line = self.env['account.invoice.line']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.voucher = self.env['account.voucher']
        self.cash_type_journal_id = self.env['account.journal'].\
            search([('type', '=', 'cash')], limit=1)[0]
        self.product_id = self.env['product.product'].\
            browse(self.ref('product.product_product_8'))

        date_start = date.today().replace(day=1, month=1).strftime('%Y-%m-%d')
        self.period_id = self.env['account.fiscalyear'].search(
            [('date_start', '=', date_start)]).period_ids[8]

        self.account_id = self.env['account.account'].\
            browse(self.ref("account.a_recv"))
        self.pay_account_id = self.env['account.account'].\
            browse(self.ref("account.cash"))
        self.journal_id = self.env['account.journal'].\
            browse(self.ref("account.bank_journal"))

    def test_01_action_ship_create(self):
        """
        Create sale order with Before Delivery policy
        """
        sale_order_id = self.sale_order.create({
            'partner_id': self.partner_id.id,
            'client_order_ref': 'TEST_SO',
            'order_policy': 'prepaid',  # 'before delivery' invoice creation
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
            })]
        })

        # confirm sale order and generate its invoice
        sale_order_id.action_button_confirm()

        for invoice_id in sale_order_id.invoice_ids:
            invoice_id.signal_workflow('invoice_open')

            # check if invoice is open
            self.assertEqual(invoice_id.state, 'open')

            # check if a journal entry have been created
            self.assertTrue(invoice_id.move_id, 'without journal entry')

            invoice_id.pay_and_reconcile(
                invoice_id.amount_total, self.pay_account_id.id,
                self.period_id.id, self.journal_id.id, self.pay_account_id.id,
                self.period_id.id, self.journal_id.id,
                name="Payment for Invoice")

            # in order to proceed is necessary to get the sale order invoiced
            # and the invoice paid as well
            self.assertTrue(sale_order_id.invoiced)
            self.assertEqual(invoice_id.state, 'paid')

            inv_lines = self.invoice_line.search(
                [('invoice_id', '=', invoice_id.id)])

            self.assertNotEqual(len(inv_lines), 0)

            failed_olines = [inv_line
                             for inv_line in invoice_id.invoice_line
                             if inv_line.move_id is False]

            # if any line is left without move_id then is something wrong
            self.assertEqual(failed_olines, [])
