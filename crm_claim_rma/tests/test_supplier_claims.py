# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Author: Yanina Aular
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
from openerp.exceptions import Warning as UserError


class TestSupplierClaims(TransactionCase):

    def setUp(self):
        super(TestSupplierClaims, self).setUp()
        self.wizard = self.env['returned.lines.from.serial.wizard']
        self.order_id = self.env.ref('purchase.purchase_order_6')
        self.invoice_id = self.order_id.invoice_ids[0]
        self.claim_id = self.env['crm.claim'].create({
            'name': 'Test for %s' % self.invoice_id.number,
            'claim_type': self.ref('crm_claim_rma.crm_claim_type_supplier'),
            'partner_id': self.invoice_id.partner_id.id,
            'pick': True
        })

    def create_wizard_for_claim(self):
        wizard_id = self.wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        lines_list_id = wizard_id.onchange_load_products(
            self.invoice_id.number + '\n', [(6, 0, [])])
        lines_list_id = lines_list_id['domain']['lines_list_id'][0][2]
        option_ids = wizard_id.onchange_load_products(
            self.invoice_id.number, [(6, 0, [])])['value']['option_ids'][0][2]
        wizard_id.option_ids = option_ids
        wizard_id.lines_list_id = [(6, 0, [lines_list_id[0]])]

        return wizard_id

    def test_02_product_without_supplier(self):
        self.invoice_id.signal_workflow('invoice_open')
        wizard_id = self.create_wizard_for_claim()
        product_with_seller_ids = self.claim_id\
            .mapped('claim_line_ids.product_id').filtered(
                lambda r: wizard_id.partner_id in r.seller_ids.mapped('name'))

        # Setting warranty duration for all product suppliers to zero,
        # and expecting a exception to be raised
        for product_id in product_with_seller_ids:
            psi_id = product_id.seller_ids.filtered(
                lambda r: r.name == wizard_id.partner_id)
            psi_id.write({'warranty_duration': 0})
        wizard_id._compute_set_message()
        error_msg = 'Supplier warranty period for one or more.*'
        with self.assertRaisesRegexp(UserError, error_msg):
            wizard_id.add_claim_lines()

        # Clean lines added to claim
        self.claim_id.claim_line_ids.unlink()

        # Unlink the all suppliers for all products and expecting an
        # exception to be raised
        for product_id in product_with_seller_ids:
            product_id.seller_ids.unlink()
        wizard_id._compute_set_message()
        with self.assertRaisesRegexp(UserError, error_msg):
            wizard_id.add_claim_lines()
