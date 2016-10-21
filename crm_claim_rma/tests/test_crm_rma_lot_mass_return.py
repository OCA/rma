# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Osval Reyes,
#            Yanina Aular
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
from openerp.exceptions import Warning as UserError
from .common import ClaimTestsCommon


class TestCrmRmaLotMassReturn(ClaimTestsCommon):

    """Test cases for CRM RMA Lot Mass Return Module
    """

    def setUp(self):
        super(TestCrmRmaLotMassReturn, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.invoice_id, self.lot_ids = self.create_sale_invoice()

    def test_01_render_metasearch_view(self):
        res = self.claim_id.render_metasearch_view()
        self.assertEqual(res['res_model'], self.metasearch_wizard._name)

    def test_02_load_products(self):

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            self.invoice_id.number +
            '*5*description here' + '\n' + self.lot_ids[0].name,
            [(6, 0, [])])

        lines_list_id = lines_list_id['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            self.invoice_id.number, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids
        wizard_id.lines_list_id = [(6, 0, lines_list_id)]

        # the invoice lines are two
        self.assertEqual(len(lines_list_id), 2)

        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id),
                         int(self.invoice_id.invoice_line.quantity))

        wizard_id._compute_set_message()

        wizard_id.add_claim_lines()

        # Claim record it must have same line count as the invoice
        qty = 0
        for inv_line in self.invoice_id.invoice_line:
            qty += inv_line.quantity
        self.assertEqual(len(self.claim_id.claim_line_ids), int(qty))

    def test_03_supplier_claim_product_addition(self):
        """Add a product to supplier claim based on a lot name related to an
        invoice line id
        """
        lot_name = 'iMac-A1090'
        sale_id = self.env.ref('crm_claim_rma.po_wizard_rma_1')
        invoice_id = sale_id.invoice_ids
        picking_id = sale_id.picking_ids[0]
        # create wizard
        wizard_id = self.env['stock.transfer_details'].create({
            'picking_id': picking_id.id,
        })
        move_id = picking_id.move_lines.filtered(
            lambda r: r.product_id.name == 'iMac')
        lot_id = self.env['stock.production.lot'].create({
            'product_id': move_id.product_id.id,
            'name': lot_name,
        })
        self.env['stock.transfer_details_items'].create({
            'transfer_id': wizard_id.id,
            'product_id': move_id.product_id.id,
            'quantity': 1,
            'sourceloc_id': move_id.location_id.id,
            'destinationloc_id': self.ref('stock.stock_location_stock'),
            'product_uom_id': move_id.product_uom.id,
            'lot_id': lot_id.id,
        })
        wizard_id.do_detailed_transfer()
        claim_id = self.create_claim(self.supplier_type, invoice_id.partner_id)

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': claim_id._name,
            'active_id': claim_id.id,
            'active_ids': claim_id.ids
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            '%s*5*damaged with problems\n' % lot_name, [(6, 0, [])])

        lines_list_id = lines_list_id['domain']['lines_list_id'][0][2]

        wizard_id.option_ids = lines_list_id
        wizard_id.lines_list_id = [(6, 0, lines_list_id)]

        wizard_id._compute_set_message()
        with self.assertRaisesRegexp(UserError, '.*'):
            wizard_id.add_claim_lines()
        self.assertEqual(len(claim_id.claim_line_ids), 1)

    def test_04_error_messages(self):
        """Test error messages when user input doesn't match with any record
        """
        sale_id = self.env.ref('crm_claim_rma.po_wizard_rma_1')
        invoice_id = sale_id.invoice_ids

        claim_id = self.create_claim(self.other_type, invoice_id.partner_id)

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': claim_id._name,
            'active_id': claim_id.id,
            'active_ids': claim_id.ids
        }).create({})

        # Input an invalid lot name
        lot_name = 'INVALID_LOT_NAME'
        lines_list_id = wizard_id.onchange_load_products(
            '%s*5*damaged with problems\n' % lot_name, [(6, 0, [])])

        error_msg = 'The product or invoice %s was not found' % lot_name
        msg = lines_list_id.get('warning', {})
        self.assertEqual(msg.get('message', ''), error_msg,
                         "Since %s doesn't exists as valid lot, a warning "
                         "message was expected" % lot_name)

        # If white spaces are introduced into wizard, empty values are returned
        lines_list_id = wizard_id.onchange_load_products('   \n', [(6, 0, [])])
        domain = lines_list_id.get('domain', {})
        value = lines_list_id.get('value', {})
        self.assertTrue(domain and value)
