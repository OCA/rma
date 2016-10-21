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
import re
from .common import ClaimTestsCommon


class TestCrmRmaLotMassReturn2(ClaimTestsCommon):

    """Test cases for CRM RMA Lot Mass Return Module
    """

    def test_01_load_products(self):
        self.transfer_po_01.do_detailed_transfer()
        self.transfer_so_01.do_detailed_transfer()
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
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

        wizard_line_ids = self.env['claim.line.wizard'].browse(lines_list_id)

        line_ids = wizard_line_ids.filtered(
            lambda r: r.lot_id.name in ['MAC0001', 'MAC0002'])
        wizard_id.lines_list_id = [(6, 0, line_ids.ids)]

        # 1 Ink Cartridge, 2 Toner Cartridge, 1 iPad, 5 iMac
        self.assertEqual(len(lines_list_id), 9)

        qty = sum(self.sale_order.invoice_ids[0].
                  invoice_line.mapped('quantity'))
        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id), int(qty))

        wizard_id._compute_set_message()
        wizard_id.add_claim_lines()
        # 2 Macs
        self.assertEqual(len(self.claim_id.claim_line_ids), 2)

        line_ids = self.claim_id.claim_line_ids
        self.assertEqual(
            set(line_ids.name_get()),
            set([(
                line_ids[0].id, "%s - %s" %
                (self.claim_id.code, line_ids[0].product_id.name)),
                (line_ids[1].id, "%s - %s" %
                 (self.claim_id.code, line_ids[1].product_id.name))
            ]))

    def test_02_load_products(self):
        self.transfer_po_01.do_detailed_transfer()
        self.transfer_so_01.do_detailed_transfer()
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        line_str = self.sale_order.invoice_ids[0].number + '*5*A description\n'
        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            line_str, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            line_str, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids
        wizard_line_ids = self.env['claim.line.wizard'].browse(lines_list_id)

        line_ids = wizard_line_ids.filtered(
            lambda r: r.lot_id.name in ['MAC0001', 'MAC0003'] or
            r.product_id.name in ['Toner Cartridge', 'Ink Cartridge'])
        wizard_id.lines_list_id = [(6, 0, line_ids.ids)]

        # 1 Ink Cartridge, 2 Toner Cartridge, 1 iPad, 5 iMac
        self.assertEqual(len(lines_list_id), 9)

        qty = sum(self.sale_order.invoice_ids[0].
                  invoice_line.mapped('quantity'))

        # Validate it has exactly as much records as the taken invoice has
        self.assertEqual(len(lines_list_id), int(qty))
        wizard_id.add_claim_lines()
        # 2 Macs
        self.assertEqual(len(self.claim_id.claim_line_ids), 5)

    def test_03_claim_line_creation_and_error_message(self):
        """Challenge the wizard when a claim line is created, to set
        claim_origin and the name correctly in a claim line itself, and also
        it tests the message displayed to the user when is introduced an
        Serial/Lot numbers that already is part of another claim.
        """

        self.transfer_po_01.do_detailed_transfer()
        self.transfer_so_01.do_detailed_transfer()
        subject_list = self.env['claim.line'].SUBJECT_LIST
        lot_name = "MAC0001"
        subject_index = 3
        scanned_data = lot_name + '*' + \
            str(subject_index) + '*A short description to test\n'
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})
        wizard_id.scan_data = scanned_data

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        wizard_id.option_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_line_ids = self.env['claim.line.wizard'].browse(lines_list_id)
        line_ids = wizard_line_ids.filtered(
            lambda r: r.lot_id.name == lot_name)
        wizard_id.lines_list_id = [(6, 0, line_ids.ids)]
        self.assertEqual(len(lines_list_id), 1)

        wizard_id.add_claim_lines()
        self.assertEqual(len(self.claim_id.claim_line_ids), 1)

        line_id = self.claim_id.claim_line_ids
        self.assertEqual(
            subject_list[subject_index - 1][0], line_id.claim_origin)
        self.assertEqual(scanned_data, line_id.prodlot_id.name + '*' +
                         str(subject_index) + '*' + line_id.name + '\n')

        # create again the wizard
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})
        wizard_id.scan_data = scanned_data

        # Get ids for invoice lines
        lines_list_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['domain']['lines_list_id'][0][2]

        wizard_id.option_id = wizard_id.onchange_load_products(
            scanned_data, [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_line_ids = self.env['claim.line.wizard'].browse(lines_list_id)
        line_ids = wizard_line_ids.filtered(
            lambda r: r.lot_id.name == lot_name)
        wizard_id.lines_list_id = [(6, 0, line_ids.ids)]
        self.assertEqual(len(lines_list_id), 1)

        wizard_id._compute_set_message()
        wizard_id.add_claim_lines()
        self.assertEqual(len(self.claim_id.claim_line_ids), 1)

        # if the message exists, then it's being displayed
        regex = re.compile(".*" + lot_name + ".*")
        self.assertTrue(regex.search(wizard_id.message))

    def test_04_load_products_from_serial_lot_number(self):
        self.transfer_po_01.do_detailed_transfer()
        self.transfer_so_01.do_detailed_transfer()
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})

        wizard_id.scaned_data = self.env['stock.production.lot'].search(
            [('name', '=', 'MAC0004')]).mapped('id')[0]

        lines_list_id = wizard_id.onchange_load_products(
            'IPAD0001\n', [(6, 0, [])]
        )['domain']['lines_list_id'][0][2]

        option_ids = wizard_id.onchange_load_products(
            'IPAD0001\n', [(6, 0, [])])['value']['option_ids'][0][2]

        wizard_id.option_ids = option_ids
        wizard_id.lines_list_id = [(6, 0, option_ids)]
        self.assertEqual(len(lines_list_id), 1)
        wizard_id.add_claim_lines()
        self.assertEqual(len(self.claim_id.claim_line_ids), 1)
        line_ids = self.claim_id.claim_line_ids
        self.assertEqual(
            set(line_ids.name_get()),
            set([(
                line_ids[0].id, "%s - %s" %
                (self.claim_id.code, line_ids[0].product_id.name)),
            ]))

    def test_05_help_buttons(self):
        """A help button is shown in wizard to let the user meets how the
        claim's wizard works, this test validates:
            - The button displays and takes the user to new window with
            the information
            - Takes the user back to the wizard
        """
        claim_id = self.claim_id
        wizard_id = self.metasearch_wizard.with_context({
            'active_model': claim_id._name,
            'active_id': claim_id.id,
            'active_ids': claim_id.ids,
        }).create({})
        button_show_help = wizard_id.button_show_help()
        help_view_id = self.ref('crm_claim_rma.help_message_form')
        context = button_show_help.get('context', {})
        self.assertEqual(button_show_help.get('view_id', -1), help_view_id)
        self.assertEqual(context.get('active_ids', []), claim_id.ids)

        button_back2wizard = wizard_id.button_get_back_to_wizard()
        context = button_back2wizard.get('context', {})
        self.assertEqual(context.get('active_ids', []), claim_id.ids)
