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
from .lot_mass_return_tests_common import LotMassReturnTestsCommon


class TestCrmRmaLotMassReturn(LotMassReturnTestsCommon):

    """ Test cases for CRM RMA Lot Mass Return Module
    """

    def setUp(self):
        super(TestCrmRmaLotMassReturn, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.partner_id = self.env['res.partner'].browse(
            self.ref('base.res_partner_2'))
        self.invoice_id, self.lot_ids = self.create_sale_invoice()
        self.claim_id = self.env['crm.claim'].\
            create({
                'name': 'Test',
                'claim_type': self.ref('crm_claim_type.'
                                       'crm_claim_type_customer'),
                'partner_id': self.invoice_id.partner_id.id,
                'pick': True
            })

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

        wizard_id._set_message()

        wizard_id.add_claim_lines()

        # Claim record it must have same line count as the invoice
        qty = 0
        for inv_line in self.invoice_id.invoice_line:
            qty += inv_line.quantity
        self.assertEqual(len(self.claim_id.claim_line_ids),
                         int(qty))
