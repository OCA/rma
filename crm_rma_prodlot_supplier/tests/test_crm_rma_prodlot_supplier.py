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


class TestCrmRmaProdLotSupplier(TransactionCase):

    """
    Test Cases
    """

    def setUp(self):
        super(TestCrmRmaProdLotSupplier, self).setUp()
        self.picking = self.env['stock.picking']

        self.picking_id1 = self.env.ref('stock.incomming_shipment1')
        self.partner_id1 = self.picking_id1.partner_id

        self.picking_id2 = self.env.ref('stock.incomming_shipment2')
        self.partner_id2 = self.picking_id2.partner_id

        self.Wizard = self.env['stock.transfer_details']
        self.transfer_item_obj = self.env['stock.transfer_details_items']
        self.lot_obj = self.env['stock.production.lot']

    def test_01_do_detail_transfer(self):
        """
        Testing supplier_id when a transfer is made
        """
        lot_ids = []
        # create wizard
        wizard = self.Wizard.create({
            'picking_id': self.picking_id1.id,
        })

        # make the transfers
        for stock_move in self.picking_id1.move_lines:
            lot_id = self.lot_obj.create({
                'product_id': stock_move.product_id.id,
            })

            # keep lot_id for later check
            lot_ids.append(lot_id)

            self.transfer_item_obj.create({
                'transfer_id': wizard.id,
                'product_id': stock_move.product_id.id,
                'quantity': stock_move.product_qty,
                'sourceloc_id': stock_move.location_id.id,
                'destinationloc_id': stock_move.location_dest_id.id,
                'lot_id': lot_id.id,
                'product_uom_id': stock_move.product_uom.id,
            })

        wizard.do_detailed_transfer()

        # check lot_ids
        failed_lot_ids = [
            lid for lid in lot_ids
            if lot_id.supplier_id.id != self.picking_id1.partner_id.id]

        self.assertEquals(failed_lot_ids, [])

    def test_02_default_get(self):
        """
        Testing supplier_id when a transfer is made
        """
        lot_ids = []
        # create wizard
        wizard = self.Wizard.with_context({
            'active_id': self.picking_id2.id,
            'active_ids': [self.picking_id2.id],
            'active_model': self.picking_id2._name
        }).create({
            'picking_id': self.picking_id2.id,
        })

        # make the transfers
        for stock_move in self.picking_id2.move_lines:

            transfer_item = self.transfer_item_obj.create({
                'transfer_id': wizard.id,
                'product_id': stock_move.product_id.id,
                'quantity': stock_move.product_qty,
                'sourceloc_id': stock_move.location_id.id,
                'destinationloc_id': stock_move.location_dest_id.id,
                'product_uom_id': stock_move.product_uom.id,
            })

            lot_id = self.lot_obj.with_context({
                'active_id': transfer_item.id
            }).create({
                'product_id': stock_move.product_id.id,
                'name': stock_move.product_id.name
            })

            # keep lot_id for later check
            lot_ids.append(lot_id)
            transfer_item.write({'lot_id': lot_id.id})

        # check lot_ids
        failed_lot_ids = [
            lid for lid in lot_ids
            if lot_id.supplier_id.id != self.picking_id2.partner_id.id]

        self.assertEquals(failed_lot_ids, [])
