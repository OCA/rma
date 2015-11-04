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


class TestLocationRma(TransactionCase):

    def setUp(self):
        super(TestLocationRma, self).setUp()
        self.warehouse = self.env['stock.warehouse']

    def test_01_create_warehouse(self):
        """
        Check if picking types were created
        """

        warehouse_id = self.warehouse.create({
            'name': 'BrandNew WH',
            'code': 'NEWWH'
        })

        self.assertTrue(warehouse_id.rma_in_type_id and
                        warehouse_id.rma_out_type_id.code and
                        warehouse_id.rma_int_type_id.code)
        self.assertEqual(warehouse_id.rma_in_type_id.code, 'incoming')
        self.assertEqual(warehouse_id.rma_out_type_id.code, 'outgoing')
        self.assertEqual(warehouse_id.rma_int_type_id.code, 'internal')
