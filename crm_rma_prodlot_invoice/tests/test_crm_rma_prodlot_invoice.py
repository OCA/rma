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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestCrmRmaProdLotInvoice(TransactionCase):

    """
    Test Cases
    """

    def setUp(self):
        super(TestCrmRmaProdLotInvoice, self).setUp()
        self.sale_order = self.env['sale.order']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.product_id = self.env['product.product'].\
            browse(self.ref('product.product_product_8'))

        date_start = date.today().replace(day=1, month=1).strftime('%Y-%m-%d')
        self.period_id = self.env['account.fiscalyear'].search(
            [('date_start', '=', date_start)]).period_ids[8]

        self.pay_account_id = self.env['account.account'].\
            browse(self.ref("account.cash"))
        self.journal_id = self.env['account.journal'].\
            browse(self.ref("account.bank_journal"))
        self.wizard = self.env['stock.transfer_details']
        self.wizard_item = self.env['stock.transfer_details_items']
        self.production_lot = self.env['stock.production.lot']
        self.purchase_order = self.env['purchase.order']
        self.picking = self.env['stock.picking']

    def create_sale_order(self, invoicing_rule='manual'):
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

    def create_purchase_order(self):
        purchase_order_id = self.purchase_order.create({
            'partner_id': self.ref('base.res_partner_1'),
            'location_id': self.ref('stock.picking_type_in'),
            'pricelist_id': 1,
            'order_line': [(0, 0, {
                'name': self.product_id.name,
                'product_id': self.product_id.id,
                'price_unit': self.product_id.list_price,
                'product_qty': 1,
                'date_planned': date.today().replace(day=31, month=12).
                strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })]
        })

        purchase_order_id.wkf_confirm_order()
        self.assertEquals(purchase_order_id.state, 'confirmed')

        purchase_order_id.action_invoice_create()
        purchase_order_id.invoice_ids.invoice_validate()
        purchase_order_id.action_picking_create()
        self.assertEquals(1, len(self.picking.
                                 search([('origin', '=',
                                          purchase_order_id.name)])))
        return purchase_order_id

    def do_whole_transfer_process(self, lot_id, picking_ids):
        """
        Do transfer process
        @param picking_ids: picking record set to be transfers
        @return Returns production lots ids for outside use/verification
        """
        for picking_id in picking_ids:

            picking_id.force_assign()
            # create wizard
            wizard_id = self.wizard.create({
                'picking_id': picking_id.id,
            })

            # make the transfers
            for move_id in picking_id.move_lines:

                self.wizard_item.create({
                    'transfer_id': wizard_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_qty,
                    'sourceloc_id': move_id.location_id.id,
                    'destinationloc_id':
                    self.ref('stock.stock_location_stock'),
                    'lot_id': lot_id and lot_id.id or False,
                    'product_uom_id': move_id.product_uom.id,
                })

            wizard_id.do_detailed_transfer()

    def get_invoices_paid(self, invoice_ids=False):
        for invoice_id in invoice_ids:
            # check if a journal entry have been created
            self.assertTrue(invoice_id.move_id)

            invoice_id.pay_and_reconcile(
                invoice_id.amount_total, self.pay_account_id.id,
                self.period_id.id, self.journal_id.id,
                self.pay_account_id.id,
                self.period_id.id, self.journal_id.id,
                name="Payment for Invoice %s" % (invoice_id.name))

            self.assertEqual(invoice_id.state, 'paid')

    def test_01_prodlot_invoice(self):
        """
        A Sale Order for a product which origin has a production lot number
        from a incoming picking.
        """
        purchase_order_id = self.create_purchase_order()

        lot_id = self.production_lot.create({
            'name': 'Lot for %s' % (purchase_order_id.name),
            'product_id': self.product_id.id,
        })

        self.do_whole_transfer_process(
            lot_id=lot_id,
            picking_ids=purchase_order_id.picking_ids)
        sale_order_id = self.create_sale_order('prepaid')

        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)
        invoice_id = sale_order_id.invoice_ids
        invoice_id.signal_workflow('invoice_open')

        self.get_invoices_paid(invoice_ids=sale_order_id.invoice_ids)

        # Check if sale order is marked as invoiced, the only way to
        # became true is when its invoices have been paid
        self.assertTrue(sale_order_id.invoiced)

        self.do_whole_transfer_process(lot_id=lot_id,
                                       picking_ids=sale_order_id.picking_ids)

        # check if invoice line if is set to the lot
        self.assertTrue(lot_id.invoice_line_id)

    def test_02_prodlot_invoice(self):
        """
        A Sale Order for a product which origin has a production lot number
        from a incoming picking.
        """
        purchase_order_id = self.create_purchase_order()

        lot_id = self.production_lot.create({
            'name': 'Lot for %s' % (purchase_order_id.name),
            'product_id': self.product_id.id,
        })
        lot_id._get_lot_complete_name()

        self.do_whole_transfer_process(
            lot_id=lot_id,
            picking_ids=purchase_order_id.picking_ids)
        sale_order_id = self.create_sale_order('manual')

        self.do_whole_transfer_process(lot_id=lot_id,
                                       picking_ids=sale_order_id.picking_ids)

        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)

        # check if lot_id have been set when creating invoice lines
        self.assertTrue(lot_id.invoice_line_id)

        # check if lot invoice line belongs to this sale order by its origin
        self.assertEquals(sale_order_id.name, lot_id.invoice_line_id.origin)

    def test_03_prodlot_invoice(self):
        """
        A Sale Order for a product which origin has a production lot number
        from a incoming picking.
        """
        purchase_order_id = self.create_purchase_order()

        lot_id = self.production_lot.create({
            'name': 'Lot for %s' % (purchase_order_id.name),
            'product_id': self.product_id.id,
        })

        self.do_whole_transfer_process(
            lot_id=lot_id,
            picking_ids=purchase_order_id.picking_ids)
        sale_order_id = self.create_sale_order('manual')

        sale_order_id.action_invoice_create()
        self.assertTrue(sale_order_id.invoice_ids)
        invoice_id = sale_order_id.invoice_ids
        invoice_id.signal_workflow('invoice_open')

        self.get_invoices_paid(invoice_ids=sale_order_id.invoice_ids)

        self.do_whole_transfer_process(lot_id=lot_id,
                                       picking_ids=sale_order_id.picking_ids)

        # check if lot_id have been set when creating invoice lines
        self.assertTrue(lot_id.invoice_line_id)

        # check if lot invoice line belongs to this sale order by its origin
        self.assertEquals(sale_order_id.name, lot_id.invoice_line_id.origin)
