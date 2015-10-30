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
from openerp.exceptions import ValidationError


class TestConstrains(TransactionCase):

    """
    - The product in claim.line.wizard must be the same
      that product of invoice line
    """

    def setUp(self):
        super(TestConstrains, self).setUp()
        self.claim_line_wizard = self.env['claim.line.wizard']

    def test_product_constrain(self):

        msg = "The product of the invoice .* is not same that product .*"
        with self.assertRaisesRegexp(ValidationError, msg):
            self.claim_line_wizard.\
                create({
                    'product_id': self.env.ref('product.'
                                               'product_product_8').id,
                    'invoice_line_id':
                    self.env.ref('account.demo_invoice_0_'
                                 'line_rpanrearpanelshe0').id,
                })
