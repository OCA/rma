# -*- coding: utf-8 -*-
# © 2015 Osval Reyes, Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
