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


class TestCrmClaimProductSupplier(TransactionCase):

    def setUp(self):
        super(TestCrmClaimProductSupplier, self).setUp()
        self.sale_order_id = self.env.ref(
            'crm_rma_lot_mass_return.so_wizard_rma_1')
        self.invoice_id = self.sale_order_id.invoice_ids[0]
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.lot_id = self.env.ref(
            'crm_rma_lot_mass_return.lot_purchase_wizard_rma_item_5')

        # Create the claim with a claim line
        self.claim_id = self.env['crm.claim'].create({
            'name': 'TEST CLAIM',
            'claim_type': self.ref('crm_claim_type.'
                                   'crm_claim_type_customer'),
            'partner_id': self.sale_order_id.partner_id.id,
        })

        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            self.lot_id.name + '\n', [(6, 0, [])]
        )['domain']['lines_list_id'][0][2]

        # Get ids for invoice lines
        lines_list_id = self.env['claim.line.wizard'].search(
            [('lot_id.name', '=', 'IPAD0001')]).mapped('id')

        wizard_id.option_ids = lines_list_id
        wizard_id.lines_list_id = [(6, 0, lines_list_id)]

        wizard_id.add_claim_lines()

    def test_01_product_supplier(self):
        claim_line_id = self.claim_id.claim_line_ids[0]
        self.assertTrue(claim_line_id.supplier_id)
        self.assertTrue(claim_line_id.supplier_invoice_id)
