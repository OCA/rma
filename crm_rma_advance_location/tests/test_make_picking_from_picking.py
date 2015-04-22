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


class TestPickingFromPicking(TransactionCase):

    def setUp(self):
        super(TestPickingFromPicking, self).setUp()
        self.stock_warehouse = self.env['stock.warehouse']
        self.crm_claim = self.env['crm.claim']
        self.wizardmakepicking = self.env['claim_make_picking.wizard']
        self.claim_picking_wizard = \
            self.env['claim_make_picking_from_picking.wizard']
        self.get_default_locations()

    def get_default_locations(self):
        """
        Create a record of product.supplier for next tests
        """
        cr, uid = self.cr, self.uid

        main_warehouse = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "stock",
                                 "warehouse0")[1]
        self.main_warehouse = self.stock_warehouse.browse(main_warehouse)

        self.loc_rma = self.main_warehouse.lot_rma_id

        self.loc_carrier_loss = self.main_warehouse.lot_carrier_loss_id

        self.loc_breakage_loss = self.main_warehouse.lot_breakage_loss_id

        self.loc_refurbish = self.main_warehouse.lot_refurbish_id

        # self.loc_mistake_loss = self.main_warehouse.lot_mistake_loss_id

        claim_test = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_claim",
                                 "crm_claim_6")[1]

        self.claim_test = self.crm_claim.browse(claim_test)

    def test_get_dest_loc(self):

        # Create Picking from Customers to RMA
        # with button New Products Return

        wiz_context = {
            'active_id': self.claim_test.id,
            'warehouse_id': self.claim_test.warehouse_id.id,
            'partner_id': self.claim_test.partner_id.id,
            'picking_type': self.claim_test.warehouse_id.rma_in_type_id.id,
        }
        wizard_id = self.wizardmakepicking.with_context(wiz_context).create({})

        # res = self.wizardmakepicking.with_context(wiz_context).\
        #     action_create_picking(wizard_id.id)
        res = wizard_id.action_create_picking()
        # res = self.wizardmakepicking.action_create_picking(
        #     [wizard_id])

        stock_picking_id = res.get('res_id')

        # Create Picking 'Product to stock'
        context = {'active_id':
                   stock_picking_id,
                   'picking_type': 'picking_stock',
                   }

        claim_wizard = self.claim_picking_wizard.\
            with_context(context).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma.id)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.main_warehouse.lot_stock_id.id)

        self.assertEquals(len(claim_wizard.picking_line_ids),
                          len(self.claim_test.claim_line_ids))

        # Review number of picking lines with claim lines
        picking_lines = claim_wizard.picking_line_ids
        claim_lines = self.claim_test.claim_line_ids

        for num in xrange(0, len(picking_lines)):
            band = False
            for num2 in xrange(0, len(claim_lines)):
                if claim_lines[num].product_id.id == \
                        picking_lines[num2].product_id.id:
                    band = True
            self.assertEquals(True, band)

        claim_wizard.with_context(context).action_create_picking_from_picking()

        # Create Picking 'Product to Loss'
        claim_wizard = self.claim_picking_wizard.\
            with_context({'active_id':
                          stock_picking_id,
                          'picking_type': 'picking_breakage_loss',
                          # self.claim_test.warehouse_id.rma_int_type_id.id,
                          }).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma.id)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.loc_breakage_loss.id)
