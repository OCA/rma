# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests import TransactionCase


class TestRMAStock(TransactionCase):

    def setUp(self):
        super(TestRMAStock, self).setUp()
        self.wh_main = self.env.ref("stock.warehouse0")

        location_model = self.env['stock.location']
        self.loc_rma = location_model.create({
            'name': 'RMA',
            'usage': 'view',
            'location_id': self.wh_main.view_location_id.id,
        })

        self.loc_box_a = location_model.create({
            'name': 'RMA - Box A',
            'usage': 'internal',
            'location_id': self.loc_rma.id,
        })

        self.loc_box_b = location_model.create({
            'name': 'RMA - Box B',
            'usage': 'internal',
            'location_id': self.loc_rma.id,
        })

        self.wh_main.lot_rma_id = self.loc_rma

        # Create products
        self.product_socket = self.env['product.product'].create({
            'name': 'Sockets',
        })

        self.product_shoes = self.env['product.product'].create({
            'name': 'Shoes',
        })

    def test_rma_qty(self):
        # Put 50 in box A
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory for Sockets',
            'location_id': self.loc_box_a.id,
            'filter': 'partial'
        })
        inventory.prepare_inventory()

        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product_socket.id,
            'location_id': self.loc_box_a.id,
            'product_qty': 50,
        })
        inventory.action_done()

        # Confirmed move for 30 in box B
        self.env['stock.move'].create({
            'name': 'Test move rma',
            'state': 'confirmed',
            'product_id': self.product_socket.id,
            'product_uom_qty': 30,
            'product_uom': self.product_socket.uom_id.id,
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': self.loc_box_b.id,
        })

        # Should have 50 avalaible and 80 forecasted
        self.assertEqual(50.0, self.product_socket.rma_qty_available)
        self.assertEqual(80.0, self.product_socket.rma_virtual_available)

        # A warehouse can be specified
        other_warehouse = self.env['stock.warehouse'].create({
            'name': 'Other warehouse',
            'partner_id': self.ref('base.main_partner'),
            'code': 'WH2',
        })

        self.assertEqual(
            0.0,
            self.product_socket.with_context(
                warehouse_id=other_warehouse.id
            ).rma_qty_available
        )
        self.assertEqual(
            0.0,
            self.product_socket.with_context(
                warehouse_id=other_warehouse.id
            ).rma_virtual_available
        )

        # Reset lot_rma_id (automatically created)
        other_warehouse.lot_rma_id = False
        self.product_socket.refresh()
        self.assertEqual(
            0.0,
            self.product_socket.with_context(
                warehouse_id=other_warehouse.id
            ).rma_qty_available
        )
        self.assertEqual(
            0.0,
            self.product_socket.with_context(
                warehouse_id=other_warehouse.id
            ).rma_virtual_available
        )

    def test_multi(self):
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory for Sockets',
            'location_id': self.loc_box_a.id,
            'filter': 'partial'
        })
        inventory.prepare_inventory()

        # Put 20 sockets and 10 shoes in box A
        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product_socket.id,
            'location_id': self.loc_box_a.id,
            'product_qty': 20,
        })
        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product_shoes.id,
            'location_id': self.loc_box_a.id,
            'product_qty': 10,
        })
        inventory.action_done()

        qties = self.env['product.product'].search_read(
            [('id', 'in', [self.product_socket.id, self.product_shoes.id])],
            ['rma_qty_available', 'rma_virtual_available'],
            order='id'
        )
        self.assertEqual([
            {'id': self.product_socket.id, 'rma_qty_available': 20,
             'rma_virtual_available': 20},
            {'id': self.product_shoes.id, 'rma_qty_available': 10,
             'rma_virtual_available': 10}
        ], qties)

    def test_variants(self):

        self.variant_shoes = self.env['product.product'].create({
            'product_tmpl_id': self.product_shoes.product_tmpl_id.id,
            'name': 'Variant shoes'
        })
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory for Sockets',
            'location_id': self.loc_box_a.id,
            'filter': 'partial'
        })
        inventory.prepare_inventory()

        # Put 5 shoes and 4 variant shoes in box A
        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product_shoes.id,
            'location_id': self.loc_box_a.id,
            'product_qty': 5,
        })
        self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.variant_shoes.id,
            'location_id': self.loc_box_a.id,
            'product_qty': 4,
        })
        inventory.action_done()

        # Confirmed move for 3 variant shoes in box B
        self.env['stock.move'].create({
            'name': 'Test move rma',
            'state': 'confirmed',
            'product_id': self.variant_shoes.id,
            'product_uom_qty': 3,
            'product_uom': self.variant_shoes.uom_id.id,
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': self.loc_box_b.id,
        })

        self.assertEqual(5.0, self.product_shoes.rma_qty_available)
        self.assertEqual(5.0, self.product_shoes.rma_virtual_available)

        self.assertEqual(4.0, self.variant_shoes.rma_qty_available)
        self.assertEqual(7.0, self.variant_shoes.rma_virtual_available)

        shoes_template = self.product_shoes.product_tmpl_id
        self.assertEqual(9.0, shoes_template.rma_qty_available)
        self.assertEqual(12.0, shoes_template.rma_virtual_available)
