# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Vauxoo
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

from openerp.tools.safe_eval import safe_eval
from .common import ClaimTestsCommon


class TestUserInput(ClaimTestsCommon):

    """This test file challenges wizard behavior when filtering invoices and
    serial lot numbers introduced by the user
    """

    def setUp(self):
        super(TestUserInput, self).setUp()
        self.wizard = self.env['returned.lines.from.serial.wizard']
        self.claim_id = self.env.ref('crm_claim.crm_claim_2')

    def test_01_user_input_cases(self):
        test_cases = [
            # Case 1: First column empty
            {
                'case': 1,
                'lines_no': 1,
                'content': """
                *  5 *                  _


                9168      """,
                'asserts': [
                    {'line': 1, 'value': "('9168', ('0', ''))"},
                ]
            },
            # Case 2: First line empty
            {
                'case': 2,
                'lines_no': 1,
                'content': """


                9898
                """,
                'asserts': [
                    {'line': 1, 'value': "('9898', ('0', ''))"},
                ]
            },
            # Case 3: Completed and alone Invoice/Lot numbers
            {
                'case': 3,
                'lines_no': 3,
                'content': """00004*5*Screen does not work
                SAJ/2016/001
                00007""",
                'asserts': [
                    {
                        'line': 1,
                        'value': "('00004', ('5', 'Screen does not work'))"
                    },
                    {
                        'line': 2,
                        'value': "('SAJ/2016/001', ('0', ''))"
                    },
                ]
            },
            # Case 4: Serial/Lot No and a reason is still valid
            {
                'case': 4,
                'lines_no': 6,
                'content': """00004*5*Screen is not working anymore
                00084*5
                SAJ/2016/001
                SAJ/2016/002*5
                SAJ/2016/003*5*The keyboard does not turn on
                00007""",
                'asserts': [
                    {'line': 2, 'value': "('00084', ('5', ''))"},
                    {'line': 4, 'value': "('SAJ/2016/002', ('5', ''))"},
                ]
            },
            # Case 5: A dot (first line) is still valid, because there is no
            # rule to minimal valid lot number (invoices have a string format)
            {
                'case': 5,
                'lines_no': 4,
                'content': """.
                00004*5*Screen does not work
                SAJ/2016/001
                00007""",
                'asserts': [
                    {'line': 1, 'value': "('.', ('0', ''))"},
                ]
            },

            # Case 6: A non-valid character as * is introduced
            {
                'case': 6,
                'lines_no': 4,
                'content': """00004*5*Screen is not working anymore
                80808*3*There is a * in the middle of the screen
                SAJ/2016/001
                00007""",
                'asserts': [
                    {'line': 2, 'value': "('80808', ('0', ''))"},
                ]
            },

            # Case 7: non-ascii chars
            {
                'case': 7,
                'lines_no': 2,
                'content': """imac2*5*áéíóú dañado
                loté*2*okok""",
                'asserts': [
                    {'line': 1, 'value': "('imac2', ('5', 'áéíóú dañado'))"},
                    {'line': 2, 'value': "('loté', ('2', 'okok'))"},
                ]
            },
        ]

        for case in test_cases:
            user_input = case['content']
            user_input = self.wizard.get_data_of_products(user_input)
            self.assertEqual(
                len(user_input), case['lines_no'],
                "Case # %s is expecting %s lines when the following user input"
                " gets parsed:\n%s" % (case['case'], case['lines_no'],
                                       case['content']))
            for item in case['asserts']:
                self.assertEqual(
                    user_input[item['line']-1], safe_eval(item['value']))

    def test_02_invoice_search_validation(self):
        invoice_id = self.sale_order.invoice_ids
        self.assertEqual(len(invoice_id), 1, 'Expected only one invoice')
        wizard_id = self.wizard.with_context({
            'active_model': self.claim_id._name,
            'active_id': self.claim_id.id,
            'active_ids': [self.claim_id.id]
        }).create({})
        res = wizard_id._get_lots_from_scan_data(invoice_id.display_name)
        self.assertEqual(len(res[0]), 9, '9 items were expected')
