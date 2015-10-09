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
        self.wizard = self.env['stock.transfer_details']
        self.wizard_item = self.env['stock.transfer_details_items']
        self.production_lot = self.env['stock.production.lot']

    def create_sale_order(self, invoicing_rule):
        # Create a sale order manual
        sale_order_id = self.sale_order.create({
            'partner_id': self.partner_id.id,
            'client_order_ref': 'TEST_SO',
            'order_policy': invoicing_rule,
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': 1
            })]
        })

        sale_order_id.action_button_confirm()

        return sale_order_id

    def test_01_prodlot_invoice(self):
        """
        Create sale order with 'On Demand' policy in order to
        test name_get for stock production lot model and do_detail_transfer
        as well.
        """

        sale_order_id = self.create_sale_order('manual')

        self.assertTrue(sale_order_id.picking_ids)
        sale_order_id.action_invoice_create()

        lot_ids = []
        lot_id = False
        for picking_id in sale_order_id.picking_ids:
            picking_id.force_assign()

            # create wizard
            wizard_id = self.wizard.create({
                'picking_id': picking_id.id,
            })

            # make the transfers
            for move_id in picking_id.move_lines:

                if not lot_id:
                    lot_id = self.production_lot.create({
                        'product_id': move_id.product_id.id,
                        'name': 'Test Lot %s%s' % (move_id.id,
                                                   move_id.product_id.id)
                    })

                    # keep lot_id for later check
                    lot_ids.append(lot_id)
                self.wizard_item.create({
                    'transfer_id': wizard_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_qty,
                    'sourceloc_id': move_id.location_id.id,
                    'destinationloc_id':
                    self.ref('stock.stock_location_stock'),
                    'lot_id': lot_id.id,
                    'product_uom_id': move_id.product_uom.id,
                })

            wizard_id.do_detailed_transfer()

        sale_order_id.action_ship_create()
        self.assertTrue(sale_order_id.invoice_ids)

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

            self.assertTrue(sale_order_id.invoiced)
            self.assertEqual(invoice_id.state, 'paid')

            inv_lines = self.invoice_line.search(
                [('invoice_id', '=', invoice_id.id)])

            self.assertNotEqual(len(inv_lines), 0)

        # assert if invoice_line_id actually have been related within the lot
        for lot_id in lot_ids:
            self.assertTrue(lot_id.invoice_line_id)

    def test_02_prodlot_invoice(self):
        """
        Create
        """
        sale_order_id = self.create_sale_order('manual')
        self.assertTrue(sale_order_id.picking_ids)

        lot_ids = []
        lot_id = False
        for picking_id in sale_order_id.picking_ids:
            picking_id.force_assign()

            # create wizard
            wizard_id = self.wizard.create({
                'picking_id': picking_id.id,
            })

            # make the transfers
            for move_id in picking_id.move_lines:

                if not lot_id:
                    lot_id = self.production_lot.create({
                        'product_id': move_id.product_id.id,
                        'name': 'Test Lot %s%s' % (move_id.id,
                                                   move_id.product_id.id)
                    })

                    # keep lot_id for later check
                    lot_ids.append(lot_id)

                self.wizard_item.create({
                    'transfer_id': wizard_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_qty,
                    'sourceloc_id': move_id.location_id.id,
                    'destinationloc_id':
                    self.ref('stock.stock_location_stock'),
                    'lot_id': lot_id.id,
                    'product_uom_id': move_id.product_uom.id,
                })

            wizard_id.do_detailed_transfer()

        # create an invoice with transfer done
        sale_order_id.action_invoice_create()

        # check if lot is related with an invoice line
        for lot_id in lot_ids:
            self.assertTrue(lot_id.invoice_line_id)

    def test_03_prodlot_invoice(self):
        """
        A Sale Order for a product which origin has a production lot number
        from a incoming picking.
        """
        pass
