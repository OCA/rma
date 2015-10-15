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


class TestCrmRmaClaimMakeClaim(TransactionCase):

    def setUp(self):
        super(TestCrmRmaClaimMakeClaim, self).setUp()
        self.metasearch_wizard = self.env['returned.lines.from.serial.wizard']
        res_partner = self.env['res.partner']
        sale_order = self.env['sale.order']
        self.supplier_id_1 = res_partner.browse(self.ref('base.res_partner_1'))
        self.supplier_id_2 = res_partner.browse(self.ref('base.res_partner_3'))
        self.supplier_id_3 = res_partner.browse(self.ref('base.res_partner_4'))
        self.claim_type = self.ref('crm_claim_type.crm_claim_type_customer')
        self.customer_id = res_partner.browse(self.ref('base.res_partner_13'))
        self.product_id = self.ref(
            'product.product_product_6_product_template')
        self.sale_order_id = sale_order.browse(self.ref('sale.sale_order_7'))
        self.sale_order_line_ids = self.sale_order_id.order_line

    def create_customer_claim(self):
        """
        Create a customer claim with or without claim lines based
        on include_lines parameter
        """

        return self.env['crm.claim'].\
            create({
                'name': 'Test Claim for %s' % (self.customer_id.name),
                'claim_type': self.claim_type,
                'partner_id': self.customer_id.id,
                'pick': True,
                'code': '/',
                'claim_line_ids': [(0, 0, {
                    'supplier_id': self.supplier_id_1.id,
                    'claim_origin': u'damaged',
                    'name': self.supplier_id_1.name,
                    'product_id': self.sale_order_line_ids[1].id
                }), (0, 0, {
                    'supplier_id': self.supplier_id_2.id,
                    'claim_origin': u'damaged',
                    'name': self.supplier_id_2.name,
                    'product_id': self.sale_order_line_ids[2].id
                }), (0, 0, {
                    'supplier_id': self.supplier_id_3.id,
                    'claim_origin': u'damaged',
                    'name': self.supplier_id_3.name,
                    'product_id': self.sale_order_line_ids[3].id
                }), ]
            })

    def test_01_claim_make_claim(self):
        claim_id = self.create_customer_claim()
        res = claim_id.claim_line_ids.button_create_line_rma_vendor()
        lines_added = eval(res[0]['domain'])[0][2]
        self.assertEquals(len(claim_id.claim_line_ids), len(lines_added))
