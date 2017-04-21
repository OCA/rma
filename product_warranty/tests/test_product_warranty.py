# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# © 2015 Vauxoo, Yanina Aular
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestProductWarranty(TransactionCase):

    def setUp(self):
        super(TestProductWarranty, self).setUp()
        self.instruction_model = self.env['return.instruction']
        self.supplierinfo = self.env['product.supplierinfo']
        self.create_product_supplierinfo()

    def create_product_supplierinfo(self):
        """
        Create a record of product.supplier for next tests
        """

        product_tmpl_id = self.env.ref('product.product_product_3')

        partner_id = self.env.ref('base.res_partner_4')
        other_partner = self.env.ref('base.res_partner_12')

        supplierinfo_data = dict(
            name=partner_id.id,
            product_name='Test SupplierInfo for display Default Instruction',
            min_qty=4,
            delay=5,
            warranty_return_partner='supplier',
            product_tmpl_id=product_tmpl_id.id,
            warranty_return_other_address=other_partner.id,
        )

        self.supplierinfo_brw = self.supplierinfo.create(supplierinfo_data)

    def test_default_instruction(self):
        """
        Test for return.instruction record with
        default field in True. If is assigned
        correctly when one record of
        product.supplierinfo is created
        """

        return_instructions_id = self.env.ref('product_warranty.'
                                              'return_instruction_1')

        self.assertEquals(self.supplierinfo_brw.return_instructions.id,
                          return_instructions_id.id)

    def test_warranty_return_address(self):
        """
        Test warranty_return_address field is calculate correctly depends of
        warranty_return_partner
        """
        self.create_product_supplierinfo()

        self.assertEquals(self.supplierinfo_brw.warranty_return_address.id,
                          self.supplierinfo_brw.name.id)

        self.supplierinfo_brw.write({'warranty_return_partner': 'company'})

        self.assertEquals(self.supplierinfo_brw.warranty_return_address.id,
                          self.supplierinfo_brw.company_id.
                          crm_return_address_id.id)

        self.supplierinfo_brw.write({'warranty_return_partner': 'other'})

        self.assertEquals(
            self.supplierinfo_brw.warranty_return_address.id,
            self.supplierinfo_brw.warranty_return_other_address.id
        )
