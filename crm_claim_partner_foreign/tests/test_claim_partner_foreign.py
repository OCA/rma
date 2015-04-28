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


class TestPartnerForeign(TransactionCase):

    def setUp(self):
        super(TestPartnerForeign, self).setUp()
        self.res_partner_obj = self.env['res.partner']
        self.get_records()

    def get_records(self):
        """
        """
        self.partner_rec = self.env.ref('base.main_partner')
        self.vauxoo_rec = self.env.ref('base.res_partner_23')
        self.claim_rec = self.env.ref('crm_claim.crm_claim_6')

    def test_claim_foreign(self):
        """
        Test if claim are national or international depends
        of main partner and partner_id  of claim
        """
        self.assertEquals(self.claim_rec.international, 'international')

        self.claim_rec.write({'partner_id': self.vauxoo_rec.id})
        self.assertEquals(self.claim_rec.international, 'national')

        country_mx = self.env.ref('base.mx')
        self.partner_rec.write({'country_id': country_mx.id})
        self.claim_rec.refresh()
        self.assertEquals(self.claim_rec.international, 'international')

