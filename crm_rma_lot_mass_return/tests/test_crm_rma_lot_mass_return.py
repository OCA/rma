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

from datetime import date
from openerp.tests.common import TransactionCase


class TestCrmRmaLotMassReturn(TransactionCase):

    """
    Test cases for CRM RMA Lot Mass Return Module
    """

    def setUp(self):
        super(TestCrmRmaLotMassReturn, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.invoice_id, self.lot_ids = self.create_sale_invoice()
        self.claim_id = self.env['crm.claim'].\
            create({
                'name': 'Test',
                'claim_type': self.ref('crm_claim_type.'
                                       'crm_claim_type_customer'),
                'partner_id': self.invoice_id.partner_id.id,
                'pick': True
            })

    def create_sale_order(self, order_policy='manual'):
        sale_order_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'note': 'Sale Order Test',
            'order_policy': order_policy,
            'payment_term': self.ref('account.account_payment_term'),
            'order_line': [(0, 0, {
                    'name': 'Test',
                    'product_id': self.ref('product.product_product_8'),
                'product_uom_qty': 2
            })]
        })

        sale_order_id.action_button_confirm()

        return sale_order_id

    def test_01_render_metasearch_view(self):
        res = self.claim_id.render_metasearch_view()
        self.assertEqual(res['res_model'], self.metasearch_wizard._name)

    def test_02_load_products(self):

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            self.invoice_id.number +
            '*5*description here' + '\n' + self.lot_ids[0].name,
            [(6, 0, [])])

        lines_list_id = lines_list_id['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            self.invoice_id.number, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids
        wizard_id.lines_list_id = [(6, 0, lines_list_id)]

        # the invoice lines are two
        self.assertEqual(len(lines_list_id), 2)

        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id),
                         int(self.invoice_id.invoice_line.quantity))

        wizard_id._compute_set_message()

        wizard_id.add_claim_lines()

        # Claim record it must have same line count as the invoice
        qty = 0
        for inv_line in self.invoice_id.invoice_line:
            qty += inv_line.quantity
        self.assertEqual(len(self.claim_id.claim_line_ids),
                         int(qty))

    def sale_validate_invoice(self, sale):

        sale_advance_obj = self.env['sale.advance.payment.inv']

        context = {
            'active_model': 'sale.order',
            'active_ids': [sale.id],
            'active_id': sale.id,
        }

        wizard_invoice_id = sale_advance_obj.with_context(context).create({
            'advance_payment_method': 'all',
        })

        wizard_invoice_id.with_context(context).create_invoices()

        invoice_id = sale.invoice_ids[0]
        invoice_id.signal_workflow('invoice_open')

        # check if invoice is open
        self.assertEqual(invoice_id.state, 'open')

        pay_account_id = self.env['account.account'].\
            browse(self.ref("account.cash"))
        journal_id = self.env['account.journal'].\
            browse(self.ref("account.bank_journal"))
        date_start = date.today().replace(day=1, month=1).strftime('%Y-%m-%d')
        period_id = self.env['account.fiscalyear'].search(
            [('date_start', '=', date_start)]).period_ids[8]

        invoice_id.pay_and_reconcile(
            invoice_id.amount_total, pay_account_id.id,
            period_id.id, journal_id.id, pay_account_id.id,
            period_id.id, journal_id.id,
            name="Payment for Invoice")

        # in order to proceed is necessary to get the sale order invoiced
        # and the invoice paid as well
        self.assertTrue(sale.invoiced)
        self.assertEqual(invoice_id.state, 'paid')

        return invoice_id

    def create_sale_invoice(self):
        sale_order_id = self.create_sale_order('manual')

        lot_ids = []
        for picking_id in sale_order_id.picking_ids:

            picking_id.force_assign()

            # create wizard
            wizard_id = self.env['stock.transfer_details'].create({
                'picking_id': picking_id.id,
            })

            # make the transfers
            for move_id in picking_id.move_lines:

                wizard_item_id = self.env['stock.transfer_details_items'].\
                    create({
                        'transfer_id': wizard_id.id,
                        'product_id': move_id.product_id.id,
                        'quantity': move_id.product_qty,
                        'sourceloc_id': move_id.location_id.id,
                        'destinationloc_id':
                        self.ref('stock.stock_location_stock'),
                        'lot_id': False,
                        'product_uom_id': move_id.product_uom.id,
                    })

                lot_id = self.env['stock.production.lot'].create({
                    'product_id': move_id.product_id.id,
                    'name': 'Test Lot %s%s' % (move_id.id,
                                               move_id.product_id.id)
                })

                # keep lot_id for later check
                lot_ids.append(lot_id)

                wizard_item_id.write({
                    'lot_id': lot_id.id
                })

            wizard_id.do_detailed_transfer()

        # Before continue, invoice must be open to get a number value
        # and this is needed by the wizard
        invoice_id = self.sale_validate_invoice(sale_order_id)

        return invoice_id, lot_ids
