# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yanina Aular
#    Copyright 2016 Vauxoo
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

from openerp.tests import common


class TestCopyMethod(common.TransactionCase):

    def setUp(self):
        super(TestCopyMethod, self).setUp()
        self.warehouse = self.env['stock.warehouse']

    def test_copy_method(self):

        partner = self.env.ref("base.res_partner_2")
        partner_address = self.env.ref("base.res_partner_12")
        claim_type_customer = self.env.ref(
            "crm_claim_rma.crm_claim_type_customer")
        sale_order_agrolait_demo = self.env.ref("sale.sale_order_1")
        invoice_agrolait = sale_order_agrolait_demo.invoice_ids[0]
        invoice_agrolait.signal_workflow("invoice_open")

        # Create the claim with a claim line
        claim_obj = self.env["crm.claim"]
        # Test code in customer claim
        claim_id = claim_obj.create(
            {
                "name": "TEST CLAIM",
                "code": "/",
                "claim_type": claim_type_customer.id,
                "delivery_address_id": partner_address.id,
                "partner_id": partner.id,
                "invoice_id": invoice_agrolait.id,
                "user_id": self.env.user.id
            })
        customer_copy = claim_id.copy()
        self.assertTrue("RMA-C" in customer_copy.code)

        # Test code in supplier claim
        claim_type_supplier = self.env.ref(
            "crm_claim_rma.crm_claim_type_supplier")
        claim_id = claim_obj.create(
            {
                "name": "TEST CLAIM",
                "code": "/",
                "claim_type": claim_type_supplier.id,
                "delivery_address_id": partner_address.id,
                "partner_id": partner.id,
                "invoice_id": invoice_agrolait.id,
                "user_id": self.env.user.id
            })
        supplier_copy = claim_id.copy()
        self.assertTrue("RMA-V" in supplier_copy.code)
