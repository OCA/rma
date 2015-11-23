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


class TestCrmRmaStockLocation(TransactionCase):

    def setUp(self):
        super(TestCrmRmaStockLocation, self).setUp()
        self.inventory = self.env['stock.inventory']
        self.inventory_line = self.env['stock.inventory.line']
        self.location_id = self.env['stock.location'].search(
            [('name', '=', 'RMA'), ('location_id.name', '=', 'WH')])
        self.warehouse_id = self.env['stock.warehouse'].browse(
            self.ref('stock.warehouse0'))
        self.lot_rma_id = self.warehouse_id.lot_rma_id
        self.product_uom_id = self.ref('product.product_uom_unit')
        self.product_socket_id = self.env['product.product'].browse(
            self.ref('crm_rma_stock_location.product_socket'))

    def test_01_test(self):
        inventory_id = self.inventory.create({
            'name': 'Test Inventory 001',
            'location_id': self.location_id.id,
            'filter': 'product',
            'product_id': self.product_socket_id.id,
        })

        inventory_line_id_a = self.inventory_line.create({
            'inventory_id': inventory_id.id,
            'product_id': self.product_socket_id.id,
            'product_uom_id': self.product_uom_id,
            'product_qty': 100,
            'location_id': self.lot_rma_id.id
        })

        inventory_line_id_b = self.inventory_line.create({
            'inventory_id': inventory_id.id,
            'product_id': self.product_socket_id.id,
            'product_uom_id': self.product_uom_id,
            'product_qty': 10,
            'location_id': self.lot_rma_id.id
        })

        inventory_id.prepare_inventory()
        inventory_id.action_done()
        qty = inventory_line_id_a.product_qty + inventory_line_id_b.product_qty
        self.assertEquals(self.product_socket_id.rma_qty_available, qty)
        self.assertEquals(self.product_socket_id.rma_virtual_available, qty)

        self.assertEquals(
            self.product_socket_id.product_tmpl_id.rma_qty_available, qty)
        self.assertEquals(
            self.product_socket_id.product_tmpl_id.rma_virtual_available, qty)

        res = self.product_socket_id._search_rma_product_quantity(
            '=',
            inventory_line_id_a.product_qty + inventory_line_id_b.product_qty)
        self.assertEquals(self.product_socket_id.id, res[0][2][0])
