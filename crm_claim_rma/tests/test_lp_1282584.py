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

        self.wizardmakepicking = self.env['claim_make_picking.wizard']
        claimline_obj = self.env['claim.line']
        claim_obj = self.env['crm.claim']

        self.product_id = self.env.ref('product.product_product_4')
        self.partner_id = self.env.ref('base.res_partner_12')

        # Create the claim with a claim line
        self.claim_id = claim_obj.create(
            {
                'name': 'TEST CLAIM',
                'number': 'TEST CLAIM',
                'claim_type': self.env.ref('crm_claim_rma.'
                                           'crm_claim_type_customer').id,
                'delivery_address_id': self.partner_id.id,
            })
        self.warehouse_id = self.claim_id.warehouse_id
        self.claim_line_id = claimline_obj.create(
            {
                'name': 'TEST CLAIM LINE',
                'claim_origine': 'none',
                'product_id': self.product_id.id,
                'claim_id': self.claim_id.id,
                'location_dest_id': self.warehouse_id.lot_stock_id.id
            })

    def test_00(self):
        """Test wizard opened view model for a new product return

        """
        wiz_context = {
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': self.warehouse_id.rma_in_type_id.id,
        }

        wizard_id = self.wizardmakepicking.with_context(wiz_context).create({})
        res = wizard_id.action_create_picking()
        self.assertEquals(res.get('res_model'),
                          'stock.picking', "Wrong model defined")

    def test_01(self):
        """Test wizard opened view model for a new delivery

        """

        wizardchangeproductqty = self.env['stock.change.product.qty']
        wiz_context = {'active_id': self.product_id}
        wizard_chg_qty_id = wizardchangeproductqty.create({
            'product_id': self.product_id.id,
            'new_quantity': 12})
        wizard_chg_qty_id.with_context(wiz_context).change_product_qty()
        wiz_context = {
            'active_id': self.claim_id.id,
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': self.warehouse_id.rma_out_type_id.id,
        }
        wizard_id = self.wizardmakepicking.with_context(wiz_context).create({})

        res = wizard_id.action_create_picking()
        self.assertEquals(res.get('res_model'),
                          'stock.picking', "Wrong model defined")
