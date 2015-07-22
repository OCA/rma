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
from openerp.tests.common import TransactionCase


class test_lp_1282584(TransactionCase):
    """ Test wizard open the right type of view

    The wizard can generate picking.in and picking.out
    Let's ensure it open the right view for each picking type
    """

    def setUp(self):
        super(test_lp_1282584, self).setUp()

        self.wizard_make_picking_obj = self.env['claim_make_picking.wizard']
        line_obj = self.env['claim.line']
        claim_obj = self.env['crm.claim']

        self.product = self.env.ref('product.product_product_4')

        self.partner = self.env.ref('base.res_partner_12')

        # Create the claim with a claim line
        self.claim = claim_obj.create(
            {
                'name': 'TEST CLAIM',
                'number': 'TEST CLAIM',
                'claim_type': 'customer',
                'delivery_address_id': self.partner.id,
            }
        )

        self.warehouse = self.claim.warehouse_id
        self.claim_line = line_obj.create(
            {
                'name': 'TEST CLAIM LINE',
                'claim_origine': 'none',
                'product_id': self.product.id,
                'claim_id': self.claim.id,
                'location_dest_id': self.warehouse.lot_stock_id.id
            }
        )

    def test_00(self):
        """ Test wizard opened view model for a new product return """
        context = {
            'active_id': self.claim.id,
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'picking_type': 'in',
        }

        wizard = self.wizard_make_picking_obj.with_context(context).create({})

        res = wizard.action_create_picking()
        self.assertEquals(res.get('res_model'), 'stock.picking',
                          "Wrong model defined")

    def test_01(self):
        """ Test wizard opened view model for a new delivery """

        wizard_change_product_qty_obj = self.env['stock.change.product.qty']
        context = {'active_id': self.product.id}
        wizard_change_product_qty = wizard_change_product_qty_obj.create({
            'product_id': self.product.id,
            'new_quantity': 12
        })

        wizard_change_product_qty.with_context(context).change_product_qty()

        context = {
            'active_id': self.claim.id,
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id,
            'picking_type': 'out',
        }

        wizard = self.wizard_make_picking_obj.with_context(context).create({})

        res = wizard.action_create_picking()
        self.assertEquals(res.get('res_model'), 'stock.picking',
                          "Wrong model defined")
