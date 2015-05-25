# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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
from openerp.tests import common


class test_picking_creation(common.TransactionCase):
    """ Test the correct pickings are created by the wizard. """

    def setUp(self):
        super(test_picking_creation, self).setUp()

        self.WizardMakePicking = self.env['claim_make_picking.wizard']
        self.StockPicking = self.env['stock.picking']
        ClaimLine = self.env['claim.line']
        Claim = self.env['crm.claim']

        self.product_id = self.env.ref('product.product_product_4')

        self.partner_id = self.env.ref('base.res_partner_12')

        self.customer_location_id = self.env.ref(
            'stock.stock_location_customers')

        # Create the claim with a claim line
        self.claim_id = Claim.create(
            {
                'name': 'TEST CLAIM',
                'number': 'TEST CLAIM',
                'claim_type': 'customer',
                'delivery_address_id': self.partner_id.id,
            })

        self.warehouse_id = self.claim_id.warehouse_id
        self.claim_line_id = ClaimLine.create(
            {
                'name': 'TEST CLAIM LINE',
                'claim_origine': 'none',
                'product_id': self.product_id.id,
                'claim_id': self.claim_id.id,
                'location_dest_id': self.warehouse_id.lot_stock_id.id,
            })

    def test_00_new_product_return(self):
        """Test wizard creates a correct picking for product return

        """
        wizard = self.WizardMakePicking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'in',
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]

        self.assertEquals(picking.location_id, self.customer_location_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id,
                          self.warehouse_id.lot_stock_id,
                          "Incorrect destination location")

    def test_01_new_delivery(self):
        """Test wizard creates a correct picking for a new delivery

        """

        WizardChangeProductQty = self.env['stock.change.product.qty']
        wizard_chg_qty = WizardChangeProductQty.with_context({
            'active_id': self.product_id.id,
        }).create({
            'product_id': self.product_id.id,
            'new_quantity': 12,
        })

        wizard_chg_qty.change_product_qty()

        wizard = self.WizardMakePicking.with_context({
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': 'out',
        }).create({})
        wizard.action_create_picking()

        self.assertEquals(len(self.claim_id.picking_ids), 1,
                          "Incorrect number of pickings created")
        picking = self.claim_id.picking_ids[0]

        self.assertEquals(picking.location_id, self.warehouse_id.lot_stock_id,
                          "Incorrect source location")
        self.assertEquals(picking.location_dest_id, self.customer_location_id,
                          "Incorrect destination location")
