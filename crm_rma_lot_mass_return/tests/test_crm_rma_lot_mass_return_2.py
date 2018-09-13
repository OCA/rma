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

from openerp.tests.common import TransactionCase
import re


class TestCrmRmaLotMassReturn2(TransactionCase):

    """
    Test cases for CRM RMA Lot Mass Return Module
    """

    def setUp(self):
        super(TestCrmRmaLotMassReturn2, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        self.sale_order = self.env.ref('crm_rma_lot_mass_return.'
                                       'so_wizard_rma_1')
        self.lot_ids_mac0001 = self.env.ref('crm_rma_lot_mass_return.'
                                            'lot_purchase_wizard_rma_item_1')
        self.lot_ids_mac0003 = self.env.ref('crm_rma_lot_mass_return.'
                                            'lot_purchase_wizard_rma_item_3')
        self.claim_id_1 = self.env['crm.claim'].\
            create({
                'name': 'CLAIM001',
                'claim_type': self.ref('crm_claim_type.'
                                       'crm_claim_type_customer'),
                'partner_id': self.sale_order.partner_id.id,
                'pick': True
            })

        self.claim_id_2 = self.env['crm.claim'].\
            create({
                'name': 'CLAIM002',
                'claim_type': self.ref('crm_claim_type.'
                                       'crm_claim_type_customer'),
                'partner_id': self.sale_order.partner_id.id,
                'pick': True
            })

    def test_01_load_products(self):
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id_1._name,
            'active_id': self.claim_id_1.id,
            'active_ids': [self.claim_id_1.id]
        }).create({})

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            self.sale_order.invoice_ids[0].number +
            '*5*description here' + '\n' + self.lot_ids_mac0001.name,
            [(6, 0, [])])['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            self.sale_order.invoice_ids[0].number +
            '*5*description here' + '\n' + self.lot_ids_mac0001.name,
            [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids

        items_to_select = self.env['claim.line.wizard'].browse(lines_list_id)

        mac0001 = items_to_select.search([('lot_id.name', '=', 'MAC0001')])
        mac0002 = items_to_select.search([('lot_id.name', '=', 'MAC0002')])
        wizard_id.lines_list_id = [(6, 0, [mac0001.id, mac0002.id])]

        # 1 Ink Cartridge, 2 Toner Cartridge, 1 iPad, 5 iMac
        self.assertEqual(len(lines_list_id), 9)

        qty = 0
        for inv_line in self.sale_order.invoice_ids[0].invoice_line:
            qty += inv_line.quantity
        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id), int(qty))

        wizard_id._compute_set_message()
        wizard_id.add_claim_lines()

        # 2 Macs
        self.assertEqual(len(self.claim_id_1.claim_line_ids), 2)

    def test_02_load_products(self):
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id_2._name,
            'active_id': self.claim_id_2.id,
            'active_ids': [self.claim_id_2.id]
        }).create({})

        line_str = self.sale_order.invoice_ids[0].number + '*5*A description\n'
        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            line_str, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            line_str, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids
        cl_wizard = self.env['claim.line.wizard'].browse(lines_list_id)

        mac0001 = cl_wizard.search([('lot_id.name', '=', 'MAC0001')])
        mac0003 = cl_wizard.search([('lot_id.name', '=', 'MAC0003')])
        toner0001 = cl_wizard.search([('product_id.name',
                                       '=', 'Toner Cartridge')])
        toner0002 = toner0001[1]
        toner0001 = toner0001[0]
        ink0001 = cl_wizard.search([('product_id.name', '=', 'Ink Cartridge')])

        wizard_id.lines_list_id = [(6, 0, [mac0001.id, mac0003.id,
                                           toner0001.id, toner0002.id,
                                           ink0001.id])]
        # 1 Ink Cartridge, 2 Toner Cartridge, 1 iPad, 5 iMac
        self.assertEqual(len(lines_list_id), 9)

        qty = 0
        for inv_line in self.sale_order.invoice_ids[0].invoice_line:
            qty += inv_line.quantity
        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id), int(qty))
        wizard_id.add_claim_lines()
        # 2 Macs
        self.assertEqual(len(self.claim_id_2.claim_line_ids), 5)

    def test_03_claim_line_creation_and_error_message(self):
        """
        Challenge the wizard when a claim line is created, to set claim_origin
        and the name correctly in a claim line itself, and also it tests the
        message displayed to the user when is introduced an Serial/Lot numbers
        that already is part of another claim.
        """

        subject_list = self.env['claim.line'].SUBJECT_LIST
        lot_name = "MAC0001"
        subject_index = 3
        scanned_data = lot_name + '*' + \
            str(subject_index) + '*A short description to test\n'
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id_2._name,
            'active_id': self.claim_id_2.id,
            'active_ids': [self.claim_id_2.id]
        }).create({})
        wizard_id.scan_data = scanned_data

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        wizard_id.option_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['value']['option_ids'][0][2]

        items_to_select = self.env['claim.line.wizard'].browse(lines_list_id)
        mac0001 = items_to_select.search([('lot_id.name', '=', lot_name)])
        wizard_id.lines_list_id = [(6, 0, [mac0001.id])]
        self.assertEqual(len(lines_list_id), 1)

        wizard_id.add_claim_lines()
        self.assertEqual(len(self.claim_id_2.claim_line_ids), 1)

        line_id = self.claim_id_2.claim_line_ids
        self.assertEqual(
            subject_list[subject_index - 1][0], line_id.claim_origin)
        self.assertEqual(scanned_data, line_id.prodlot_id.name + '*' +
                         str(subject_index) + '*' + line_id.name + '\n')

        # create again the wizard
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id_2._name,
            'active_id': self.claim_id_2.id,
            'active_ids': [self.claim_id_2.id]
        }).create({})
        wizard_id.scan_data = scanned_data

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        wizard_id.option_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['value']['option_ids'][0][2]

        cl_wizard = self.env['claim.line.wizard'].browse(lines_list_id)
        clw_id = cl_wizard.search([('lot_id.name', '=', lot_name)])
        wizard_id.lines_list_id = [(6, 0, [clw_id.id])]
        self.assertEqual(len(lines_list_id), 1)

        wizard_id._compute_set_message()
        wizard_id.add_claim_lines()
        self.assertEqual(len(self.claim_id_2.claim_line_ids), 1)

        # if the message exists, then it's being displayed
        regex = re.compile(".*" + lot_name + ".*")
        self.assertTrue(regex.search(wizard_id.message))
