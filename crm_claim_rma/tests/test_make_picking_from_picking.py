# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yanina Aular
#    Copyright 2015 Vauxoo
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
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning as UserError


class TestPickingFromPicking(TransactionCase):

    def setUp(self):
        super(TestPickingFromPicking, self).setUp()
        self.stock_warehouse = self.env['stock.warehouse']
        self.claim_id = self.create_claim()
        self.wizardmakepicking = self.env['claim_make_picking.wizard']
        self.claim_picking_wizard = \
            self.env['claim.make.picking.from.picking.wizard']
        self.get_default_locations()

    def create_claim(self):
        claim_id = self.env['crm.claim'].browse(
            self.ref("crm_claim.crm_claim_6"))

        claim_id.write({
            'claim_line_ids': [(0, 0, {
                'name': str(claim_id.id) + 'test 1',
                'claim_origin': u'damaged',
                'product_id': self.ref('product.product_product_8')
            }), (0, 0, {
                'name': str(claim_id.id) + 'test 2',
                'claim_origin': u'none',
                'product_id': self.ref('product.product_product_6')
            })]
        })

        return claim_id

    def get_default_locations(self):
        """Return locations for RMA, Loss and Refurbish
        """
        self.main_warehouse_id = self.stock_warehouse.browse(
            self.ref("stock.warehouse0"))

        self.loc_rma = self.main_warehouse_id.lot_rma_id
        self.loss_loc = self.main_warehouse_id.loss_loc_id
        self.loc_refurbish = self.main_warehouse_id.lot_refurbish_id

    def create_picking_wizard(self, claim_id):
        """Create a picking based on claim
        """
        wizard_id = self.wizardmakepicking.with_context({
            'active_id': claim_id.id,
            'warehouse_id': claim_id.warehouse_id.id,
            'partner_id': claim_id.partner_id.id,
            'picking_type': claim_id.warehouse_id.rma_in_type_id.id,
        }).create({})
        res = wizard_id.action_create_picking()

        return wizard_id, res

    def test_01_get_dest_loc(self):
        """Create picking from customers to rma location with button
        new products return
        """
        wizard_id, res = self.create_picking_wizard(self.claim_id)
        stock_picking_id = res.get('res_id')
        self.assertTrue(wizard_id)
        # It's not allowed to create product return twice
        error_msg = ".*A picking has already been created for this claim.*"
        with self.assertRaisesRegexp(UserError, error_msg):
            self.create_picking_wizard(self.claim_id)

        # Create Picking 'Product to stock'
        context = {
            'active_id': stock_picking_id,
            'picking_type': 'picking_stock',
        }

        claim_wizard = self.claim_picking_wizard.\
            with_context(context).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma.id)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.main_warehouse_id.lot_stock_id.id)

        self.assertEquals(len(claim_wizard.picking_line_ids),
                          len(self.claim_id.claim_line_ids))

        # Review number of picking lines with claim lines
        picking_lines = claim_wizard.picking_line_ids
        claim_lines = self.claim_id.claim_line_ids

        claim_line_product_ids = claim_lines.mapped('product_id.id')
        picking_product_in_claim_line_ids = picking_lines.filtered(
            lambda r: r.product_id.id in claim_line_product_ids)
        self.assertEquals(picking_product_in_claim_line_ids, picking_lines)

        claim_wizard.with_context(context).action_create_picking_from_picking()

        # Create Picking 'Product to Loss'
        claim_wizard = self.claim_picking_wizard.\
            with_context({
                'active_id': stock_picking_id,
                'picking_type': 'picking_loss',
            }).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma.id)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.loss_loc.id)

    def assert_picking_type(self, picking_type_str=''):
        new_context = {
            'active_id': self.claim_id.id,
            'warehouse_id': self.claim_id.warehouse_id.id,
            'partner_id': self.claim_id.partner_id.id,
            'picking_type': picking_type_str,
        }
        wizard_id = self.wizardmakepicking.with_context(new_context).create({})
        eval_string = ('self.claim_id.warehouse_id.rma_%s_'
                       'type_id.default_location_dest_id') % picking_type_str
        default_location_dest_id = safe_eval(eval_string, {"self": self})
        self.assertEquals(
            wizard_id.claim_line_dest_location_id, default_location_dest_id)

    def test_02_picking_types_in_out_int(self):
        self.assert_picking_type('in')
        # TODO fix this tests because when the claim_type is customer
        # or supplier the destination is not same
        # self.assert_picking_type('out')
        self.assert_picking_type('int')

    def test_03_picking_type_loss(self):
        new_context = {
            'active_id': self.claim_id.id,
            'warehouse_id': self.claim_id.warehouse_id.id,
            'partner_id': self.claim_id.partner_id.id,
            'picking_type': 'loss',
        }
        wizard_id = self.wizardmakepicking.with_context(new_context).create({})
        default_location_dest_id = self.claim_id.warehouse_id.loss_loc_id
        self.assertEquals(
            wizard_id.claim_line_dest_location_id, default_location_dest_id)
