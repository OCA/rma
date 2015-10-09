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


class TestCrmRmaProdLotSupplier(TransactionCase):

    def setUp(self):
        super(TestCrmRmaProdLotSupplier, self).setUp()
        self.picking = self.env['stock.picking']
        self.wizard = self.env['stock.transfer_details']
        self.wizard_item = self.env['stock.transfer_details_items']
        self.production_lot = self.env['stock.production.lot']
        self.purchase_order = self.env['purchase.order']
        self.product_id = self.env['product.product'].\
            browse(self.ref('product.product_product_8'))
        self.purchase_order_id = self.create_purchase_order()

    def create_purchase_order(self):
        purchase_order_id = self.purchase_order.create({
            'partner_id': self.ref('base.res_partner_1'),
            'location_id': self.ref('stock.picking_type_in'),
            'pricelist_id': 1,
            'order_line': [(0, 0, {
                'name': 'test',
                'product_id': self.product_id.id,
                'price_unit': self.product_id.list_price,
                'product_qty': 16,
                'date_planned': date.today().replace(day=31, month=12).
                strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })]
        })

        purchase_order_id.wkf_confirm_order()
        purchase_order_id.action_invoice_create()
        purchase_order_id.action_picking_create()
        self.assertEquals(purchase_order_id.state, 'confirmed')
        self.assertEquals(1, len(self.picking.
                                 search([('origin', '=',
                                          purchase_order_id.name)])))
        self.picking_ids = purchase_order_id.picking_ids
        return purchase_order_id

    def test_01_do_detail_transfer(self):
        """
        Testing do_detailed_transfer method
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
        """
        Test default_get method
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

        self.assertEquals(failed_lot_ids, [])
