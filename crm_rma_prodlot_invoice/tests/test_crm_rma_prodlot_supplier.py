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

from datetime import date
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestCrmRmaProdLotSupplier(TransactionCase):

    def setUp(self):
        super(TestCrmRmaProdLotSupplier, self).setUp()
        self.picking = self.env['stock.picking']
        self.wizard = self.env['stock.transfer_details']
        self.wizard_item = self.env['stock.transfer_details_items']
        self.production_lot = self.env['stock.production.lot']
        self.purchase_order = self.env['purchase.order']
        self.imac = self.env.ref('product.product_product_8')
        self.purchase_order_id = self.create_purchase_order()

    def create_purchase_order(self):
        purchase_order_id = self.purchase_order.create({
            'partner_id': self.ref('base.res_partner_1'),
            'location_id': self.ref('stock.picking_type_in'),
            'pricelist_id': 1,
            'order_line': [(0, 0, {
                'name': 'test',
                'product_id': self.imac.id,
                'price_unit': self.imac.list_price,
                'product_qty': 16,
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

    def test_01_do_detail_transfer(self):
        """Testing do_detailed_transfer method
        """
        lot_ids = []
        for picking_id in self.picking_ids:
            # create wizard
            wizard_id = self.wizard.create({
                'picking_id': picking_id.id,
            })

            # make the transfers
            for move_id in picking_id.move_lines:
                lot_id = self.production_lot.create({
                    'product_id': move_id.product_id.id,
                })

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

                # keep lot_id for later check
                lot_ids.append(lot_id)

            wizard_id.do_detailed_transfer()

            # check lot_ids
            failed_lot_ids = [
                lid for lid in lot_ids
                if not lid.supplier_id or not
                lid.supplier_invoice_line_id]

        self.assertEquals(failed_lot_ids, [])

    def test_02_default_get(self):
        """Test default_get method
        """

        failed_lot_ids = lot_ids = []

        # make the transfers
        for picking_id in self.picking_ids:

            wizard_id = self.wizard.create({
                'picking_id': picking_id.id
            })

            for move_id in picking_id.move_lines:

                wizard_item_id = self.wizard_item.create({
                    'transfer_id': wizard_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_qty,
                    'sourceloc_id': move_id.location_id.id,
                    'destinationloc_id':
                    self.ref('stock.stock_location_stock'),
                    'lot_id': False,
                    'product_uom_id': move_id.product_uom.id,
                })

                lot_id = self.production_lot.with_context({
                    'active_model': wizard_item_id._name,
                    'active_id': wizard_item_id.id,
                    'product_id': move_id.product_id.id
                }).create({
                    'name': 'Transfer for ' + self.purchase_order_id.name
                })

                # keep lot_id for later check
                lot_ids.append(lot_id)

            wizard_id.do_detailed_transfer()

            # check lot_ids
            failed_lot_ids = [
                lid for lid in lot_ids
                if not lid.supplier_id or not
                lid.supplier_invoice_line_id]

        self.assertEquals(failed_lot_ids, lot_ids)

    def test_03_action_create_invoice(self):
        """Testing action_create_invoice method
        """

        ipad = self.env.ref('product.product_product_6')
        ipod = self.env.ref('product.product_product_11')
        date_planned = date.today().replace(day=31, month=12).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)

        purchase_order_id = self.purchase_order.create({
            'partner_id': self.ref('base.res_partner_1'),
            'location_id': self.ref('stock.picking_type_in'),
            'pricelist_id': 1,
            'invoice_method': 'picking',
            'order_line': [
                (0, 0, {
                    'name': 'imac',
                    'product_id': self.imac.id,
                    'price_unit': self.imac.list_price,
                    'product_qty': 3,
                    'date_planned': date_planned,
                    }),
                (0, 0, {
                    'name': 'ipad',
                    'product_id': ipad.id,
                    'price_unit': ipad.list_price,
                    'product_qty': 2,
                    'date_planned': date_planned,
                    }),
                (0, 0, {
                    'name': 'ipod',
                    'product_id': ipod.id,
                    'price_unit': ipod.list_price,
                    'product_qty': 4,
                    'date_planned': date_planned,
                    }),
            ]
        })

        purchase_order_id.signal_workflow("purchase_confirm")
        self.assertEquals(purchase_order_id.state, 'approved')

        lot_ids = []
        for picking_id in purchase_order_id.picking_ids:

            picking_id.write({"invoice_state": "2binvoiced"})
            wizard_id = self.wizard.create({
                'picking_id': picking_id.id
            })

            for move_id in picking_id.move_lines:
                move_id.write({"invoice_state": "2binvoiced"})
                ii = 0
                while ii < int(move_id.product_qty):
                    ii += 1
                    wizard_item_id = self.wizard_item.create({
                        'transfer_id': wizard_id.id,
                        'product_id': move_id.product_id.id,
                        'quantity': 1.0,
                        'sourceloc_id': move_id.location_id.id,
                        'destinationloc_id':
                        self.ref('stock.stock_location_stock'),
                        'lot_id': False,
                        'product_uom_id': move_id.product_uom.id,
                    })
                    lot_id = self.production_lot.with_context({
                        'active_model': wizard_item_id._name,
                        'active_id': wizard_item_id.id,
                        'product_id': move_id.product_id.id
                    }).create({
                        'name': 'LOT' + str(wizard_item_id.id)
                    })
                    wizard_item_id.write({
                        'lot_id': lot_id.id,
                    })
                    # keep lot_id for later check
                    lot_ids.append(lot_id)

            wizard_id.do_detailed_transfer()

            ctx = {
                "active_id": picking_id.id,
                "active_ids": [picking_id.id],
                "active_model": "stock.picking",
            }
            onshipping = self.env["stock.invoice.onshipping"]
            create_invoice_wizard = onshipping.with_context(ctx).create({
            })
            create_invoice_wizard.open_invoice()

            invoice_lines = purchase_order_id.mapped(
                "invoice_ids.invoice_line")

            self.review_that_lots_have_supplier_invoice_line(
                invoice_lines)

            # Call again for tests that lot with supplier invoice line
            # do not enter int ther process of assign supplier invoice
            # line
            picking_id._search_serial_number_to_change_from_picking(
                purchase_order_id.mapped("invoice_ids.id"), 'in_invoice')

            picking_id._search_serial_number_to_change_from_picking(
                purchase_order_id.mapped("invoice_ids.id"), 'out_refund')

            self.review_that_lots_have_supplier_invoice_line(invoice_lines)

    def review_that_lots_have_supplier_invoice_line(self, invoice_lines):
        for invoice_line in invoice_lines:
            lots = self.production_lot.search(
                [("supplier_invoice_line_id",
                    "=", invoice_line.id)])
            self.assertEquals(len(lots), int(invoice_line.quantity))
            self.assertEquals(
                lots.mapped("supplier_invoice_line_id"),
                invoice_line)
