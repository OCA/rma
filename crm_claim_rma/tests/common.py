# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Vauxoo
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
from datetime import date
from openerp.tests.common import TransactionCase


class ClaimTestsCommon(TransactionCase):

    """Common data in use for unit testing
    """

    def setUp(self):
        super(ClaimTestsCommon, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']

        self.payment_acct_id = self.env.ref("account.cash")
        self.journal_id = self.env.ref("account.bank_journal")
        self.period_id = self.env.ref('account.period_10')
        self.rma_customer_id = self.env['res.partner'].create({
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
        self.invoice_id, self.lot_ids = self.create_sale_invoice()

        # data for new sale order with custom lines
        order_vals = {
            'name': 'SOWIZARDCLAIM001',
            'partner_id': self.rma_customer_id.id,
        }

        product_vals = [{
            'product_id': self.ref('product.product_product_38'),
            'qty': 1,
            'price': 65.0,
        }, {
            'product_id': self.ref('product.product_product_39'),
            'qty': 2,
            'price': 66.0,
        }, {
            'product_id': self.ref('product.product_product_6'),
            'qty': 1,
            'price': 800.0,
        }, {
            'product_id': self.ref('product.product_product_8'),
            'qty': 5,
            'price': 1299.0,
        }]

        self.sale_order = self.create_and_process_sale(order_vals,
                                                       product_vals)

        self.lot_ids_mac0001 = self.env.ref('crm_claim_rma.'
                                            'lot_purchase_wizard_rma_item_1')
        self.lot_ids_mac0003 = self.env.ref('crm_claim_rma.'
                                            'lot_purchase_wizard_rma_item_3')
        self.other_type = self.env.ref(
            'crm_claim_rma.crm_claim_type_other')
        self.customer_type = self.env.ref(
            'crm_claim_rma.crm_claim_type_customer')
        self.supplier_type = self.env.ref(
            'crm_claim_rma.crm_claim_type_supplier')
        self.claim_id = self.create_claim(self.customer_type,
                                          self.rma_customer_id,
                                          name='Test Claim 001')
        self.transfer_po_01 = self.env.ref(
            'crm_claim_rma.transfer_purchase_wizard_rma')

        # Data relation for every product there is a N-lots available
        self.rma_lot_ids = {
            self.ref('product.product_product_6'): [
                self.ref('crm_claim_rma.lot_purchase_wizard_rma_item_5')
            ],
            self.ref('product.product_product_8'): [
                self.ref('crm_claim_rma.lot_purchase_wizard_rma_item_1'),
                self.ref('crm_claim_rma.lot_purchase_wizard_rma_item_2'),
                self.ref('crm_claim_rma.lot_purchase_wizard_rma_item_3'),
                self.ref('crm_claim_rma.lot_purchase_wizard_rma_item_4'),
            ]
        }
        self.transfer_so_01 = self.assign_sale_as_unique_and_transfer(
            self.sale_order, self.rma_lot_ids)

    def create_claim(self, claim_type, partner_id, address_id=False,
                     name='Test', invoice_id=False):
        return self.env['crm.claim'].create({
            'name': name,
            'claim_type': claim_type.id,
            'partner_id': partner_id.id,
            'invoice_id': invoice_id and invoice_id.id,
            'delivery_address_id': address_id and address_id.id,
            'pick': not address_id
        })

    def create_sale_order(self, partner_id, order_policy='manual'):
        sale_order_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
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
        sale_order_id = self.create_sale_order(self.rma_customer_id, 'manual')

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

    def create_and_process_sale(self, order_vals, product_vals):
        order_id = self.env['sale.order'].create({
            'name': order_vals.get('name'),
            'date_order': '2015-05-08 18:17:05',
            'partner_id': order_vals.get('partner_id'),
            'currency_id': self.ref('base.EUR'),
            'pricelist_id': self.ref('product.list0')
        })

        index = 1
        for product in product_vals:
            self.env['sale.order.line'].create({
                'name': '%s line %s' % (order_id.name, str(index)),
                'order_id': order_id.id,
                'product_id': product.get('product_id'),
                'product_uom_qty': product.get('qty'),
                'price_unit': product.get('price'),
            })
            index += 1

        order_id.signal_workflow('order_confirm')
        order_id.signal_workflow('manual_invoice')
        invoice_id = order_id.invoice_ids[0]
        invoice_id.signal_workflow('invoice_open')
        picking_id = order_id.picking_ids[0]
        picking_id.action_assign()

        invoice_id.pay_and_reconcile(
            invoice_id.amount_total,
            self.payment_acct_id.id, self.period_id.id, self.journal_id.id,
            self.payment_acct_id.id, self.period_id.id, self.journal_id.id,
            name="Payment for Invoice")

        return order_id

    def assign_sale_as_unique_and_transfer(self, sale_order, lot_ids=False):
        source_location_id = self.ref('stock.stock_location_stock')
        target_location_id = self.ref('stock.stock_location_customers')
        wizard_id = self.env['stock.transfer_details'].create({
            'picking_id': self.env['stock.picking'].search([
                ('origin', '=', sale_order.name)]).id,
        })

        # keep in a list the product_ids based on their quantities
        product_2b_assigned = []
        for line_id in sale_order.order_line:
            product_2b_assigned.extend(
                [line_id.product_id.id] * int(line_id.product_uom_qty))

        for product_id in product_2b_assigned:
            lot_id = lot_ids.get(product_id, False)
            self.env['stock.transfer_details_items'].create({
                'transfer_id': wizard_id.id,
                'quantity': 1,
                'product_id': product_id,
                'product_uom_id': self.ref('product.product_uom_unit'),
                'sourceloc_id': source_location_id,
                'destinationloc_id': target_location_id,
                'lot_id': lot_id and lot_id.pop(0)
            })
        return wizard_id
