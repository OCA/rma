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

from openerp.tests.common import TransactionCase


class TestMailMessages(TransactionCase):
    def setUp(self):
        super(TestMailMessages, self).setUp()
        self.claim_id = self.env.ref('crm_claim.crm_claim_2')
        self.partner_id = self.claim_id.partner_id

    def validate_suggested_recipients(self, recipients, claim_id, reason_str):
        recipients = recipients.items()[0]
        self.assertEqual(recipients[0], claim_id.id)
        rid, name_mail, reason = recipients[1][0]
        self.assertTrue(rid)
        self.assertEqual(name_mail, 'OpenElec Applications<openelecapplication'
                         's@yourcompany.example.com>')
        self.assertEqual(reason, reason_str)

    def test_01_suggested_recipients(self):
        """Validate suggested recipients to reply on
        """
        recipients = self.claim_id.message_get_suggested_recipients()
        self.validate_suggested_recipients(recipients, self.claim_id,
                                           'Customer')

    def test_02_suggested_recipients_without_partner(self):
        """Validate suggested mail recipients based on claim but not having
        the partner set (Partner isn't required in model, but View does)
        """
        self.claim_id.write({'partner_id': False})
        recipients = self.claim_id.message_get_suggested_recipients()
        self.assertEqual(recipients, {2: []})
