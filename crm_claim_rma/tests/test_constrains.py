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
from openerp.exceptions import ValidationError, Warning as UserError


class TestConstrains(TransactionCase):

    """- The product in claim.line.wizard must be the same
      that product of invoice line
    """

    def setUp(self):
        super(TestConstrains, self).setUp()
        self.claim_id = self.env.ref('crm_claim.crm_claim_3')

    def test_01_product_constrain(self):

        msg = "The product of the invoice .* is not same that product .*"
        with self.assertRaisesRegexp(ValidationError, msg):
            self.env['claim.line.wizard'].create({
                'product_id': self.env.ref('product.product_product_8').id,
                'invoice_line_id': self.env.ref('account.demo_invoice_0_'
                                                'line_rpanrearpanelshe0').id,
            })

    def try_set_warranty(self, vals):
        line_id = self.claim_id.claim_line_ids[0]
        field_id = getattr(line_id, vals['field_name'])
        line_id.write({vals['field_name']: False})
        with self.assertRaisesRegexp(UserError, vals['error_msg']):
            line_id.set_warranty()
        line_id.write({vals['field_name']: field_id.id})
        line_id.set_warranty()

    def test_02_missing_product(self):
        """An error should be thrown when computing warranty and there is no
        product set in a claim line
        """
        self.try_set_warranty({
            'field_name': 'product_id',
            'error_msg': 'Please set product first'
        })

    def test_03_missing_invoice_line(self):
        """An error should be thrown when computing warranty and there is no
        invoice line set in a claim line
        """
        self.try_set_warranty({
            'field_name': 'invoice_line_id',
            'error_msg': 'Please set invoice first'
        })

    def test_04_limit_days_zero(self):
        """An exception should be raised when limit_days reaches a value of
        zero (or less) when is set
        """
        company_ids = self.env['res.company'].search([])
        error_msg = 'Limit days must be greater than zero'
        with self.assertRaisesRegexp(ValidationError, error_msg):
            company_ids.write({'limit_days': 0})
