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


class TestProductWarranty(TransactionCase):

    def setUp(self):
        super(TestProductWarranty, self).setUp()
        self.instruction_model = self.env['return.instruction']
        self.supplierinfo = self.env['product.supplierinfo']
        self.create_product_supplierinfo()

    def create_product_supplierinfo(self):
        """Create a record of product.supplier for next tests
        """

        product_tmpl_id = self.env.ref('product.product_product_3')

        partner_id = self.env.ref('base.res_partner_4')

        supplierinfo_data = dict(name=partner_id.id,
                                 product_name='Test SupplierInfo for'
                                 ' display Default Instruction',
                                 min_qty=4,
                                 delay=5,
                                 warranty_return_partner='supplier',
                                 product_tmpl_id=product_tmpl_id.id,)
        self.supplierinfo_brw = \
            self.supplierinfo.create(supplierinfo_data)

    def test_default_instruction(self):
        """Test for return.instruction record with
        default field in True. If is assigned
        correctly when one record of
        product.supplierinfo is created
        """

        return_instructions_id = self.env.ref('product_warranty.'
                                              'return_instruction_1')

        self.assertEquals(self.supplierinfo_brw.return_instructions.id,
                          return_instructions_id.id)

    def test_warranty_return_address(self):
        """Test warranty_return_address field is calculate correctly depends of
        warranty_return_partner
        """
        self.create_product_supplierinfo()

        self.assertEquals(self.supplierinfo_brw.warranty_return_address.id,
                          self.supplierinfo_brw.name.id)

        self.supplierinfo_brw.write({'warranty_return_partner': 'company'})

        self.assertEquals(self.supplierinfo_brw.warranty_return_address.id,
                          self.supplierinfo_brw.company_id.
                          crm_return_address_id.id)
