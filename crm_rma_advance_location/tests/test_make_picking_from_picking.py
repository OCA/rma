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

        self.loc_rma = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_rma_location_rma",
                                 "stock_location_rma")[1]

        self.loc_carrier_loss = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_rma_advance_location",
                                 "stock_location_carrier_loss")[1]

        self.loc_breakage_loss = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_rma_advance_location",
                                 "stock_location_breakage_loss")[1]

        self.loc_refurbish = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_rma_advance_location",
                                 "stock_location_refurbish")[1]

        self.loc_mistake_loss = self.registry("ir.model.data").\
            get_object_reference(cr, uid, "crm_rma_advance_location",
                                 "stock_location_mistake_loss")[1]

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
            'picking_type': 'in',
        }
        wizard_id = self.wizardmakepicking.with_context(wiz_context).create({})

        res = wizard_id.action_create_picking()

        stock_picking_id = res.get('res_id')

        context = {'active_id':
                   stock_picking_id,
                   'picking_type':
                   'picking_stock'}

        # Create Picking 'Product to stock'
        claim_wizard = self.claim_picking_wizard.\
            with_context(context).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.main_warehouse.lot_stock_id.id)

        self.assertEquals(len(claim_wizard.picking_line_ids),
                          len(self.claim_test.claim_line_ids))

        # Review number of picking lines with claim lines
        picking_lines = claim_wizard.picking_line_ids
        claim_lines = self.claim_test.claim_line_ids

        for num in xrange(0, len(picking_lines)):
            self.assertEquals(claim_lines[num].product_id.id,
                              picking_lines[num].product_id.id)

        # TODO it is not wirking because the method
        # action_create_picking_from_picking
        # must has a picking_type_id
        # claim_wizard.with_context(context).action_create_picking_from_picking()

        # Create Picking 'Product to Loss'
        claim_wizard = self.claim_picking_wizard.\
            with_context({'active_id':
                          stock_picking_id,
                          'picking_type':
                          'picking_breakage_loss'}).create({})

        self.assertEquals(claim_wizard.picking_line_source_location.id,
                          self.loc_rma)

        self.assertEquals(claim_wizard.picking_line_dest_location.id,
                          self.loc_breakage_loss)
