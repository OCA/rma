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


class test_lp_1282584(common.TransactionCase):

    """ Test wizard open the right type of view

    The wizard can generate picking.in and picking.out
    Let's ensure it open the right view for each picking type
    """

    def setUp(self):
        super(test_lp_1282584, self).setUp()
        cr, uid = self.cr, self.uid

        self.wizardmakepicking = self.registry('claim_make_picking.wizard')
        claimline_obj = self.registry('claim.line')
        claim_obj = self.registry('crm.claim')

        self.product_id = self.ref('product.product_product_4')

        self.partner_id = self.ref('base.res_partner_12')

        # Create the claim with a claim line
        self.claim_id = claim_obj.create(
            cr, uid,
            {
                'name': 'TEST CLAIM',
                'number': 'TEST CLAIM',
                'claim_type': 'customer',
                'delivery_address_id': self.partner_id,
            })

        claim = claim_obj.browse(cr, uid, self.claim_id)
        self.warehouse_id = claim.warehouse_id
        self.claim_line_id = claimline_obj.create(
            cr, uid,
            {
                'name': 'TEST CLAIM LINE',
                'claim_origine': 'none',
                'product_id': self.product_id,
                'claim_id': self.claim_id,
                'location_dest_id': claim.warehouse_id.lot_stock_id.id
            })

    def test_00(self):
        """Test wizard opened view model for a new product return

        """
        cr, uid = self.cr, self.uid
        wiz_context = {
            'active_id': self.claim_id,
            'partner_id': self.partner_id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': self.warehouse_id.rma_in_type_id.id,
        }

        wizard_id = self.wizardmakepicking.create(cr, uid, {
        }, context=wiz_context)

        res = self.wizardmakepicking.action_create_picking(
            cr, uid, [wizard_id], context=wiz_context)
        self.assertEquals(res.get('res_model'),
                          'stock.picking', "Wrong model defined")

    def test_01(self):
        """Test wizard opened view model for a new delivery

        """

        cr, uid = self.cr, self.uid

        wizardchangeproductqty = self.registry('stock.change.product.qty')
        wiz_context = {'active_id': self.product_id}
        wizard_chg_qty_id = wizardchangeproductqty.create(cr, uid, {
            'product_id': self.product_id,
            'new_quantity': 12})
        wizardchangeproductqty.change_product_qty(
            cr, uid, [wizard_chg_qty_id], context=wiz_context)

        wiz_context = {
            'active_id': self.claim_id,
            'partner_id': self.partner_id,
            'warehouse_id': self.warehouse_id.id,
            'picking_type': self.warehouse_id.rma_out_type_id.id,
        }
        wizard_id = self.wizardmakepicking.create(cr, uid, {
        }, context=wiz_context)

        res = self.wizardmakepicking.action_create_picking(
            cr, uid, [wizard_id], context=wiz_context)
        self.assertEquals(res.get('res_model'),
                          'stock.picking', "Wrong model defined")
