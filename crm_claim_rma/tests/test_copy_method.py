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

from .common import ClaimTestsCommon


class TestCopyMethod(ClaimTestsCommon):

    def setUp(self):
        super(TestCopyMethod, self).setUp()
        self.warehouse = self.env['stock.warehouse']

    def test_01_claim_line_copy(self):
        """ Copy a claim line and validate fields values
            move_in_id -> False
            move_out_id -> False
            refund_line_id -> False
        """
        line_ids = self.env.ref('crm_claim.crm_claim_6').claim_line_ids
        line_id = line_ids[1]
        line_copied_id = line_id.copy()

        # If you need more fields to be expected as false, insert them below
        fields = ['move_in_id',
                  'move_out_id',
                  'refund_line_id']
        fields_without_value = [getattr(line_copied_id, fd) for fd in fields]
        self.assertFalse(
            any(fields_without_value),
            'One or more fields in %s has value not expected' % str(fields))

    def test_02_claim_document_copy(self):
        claim_type_customer = self.env.ref(
            "crm_claim_rma.crm_claim_type_customer")
        sale_id = self.create_sale_order(self.rma_customer_id)
        sale_id.signal_workflow('manual_invoice')
        invoice_id = sale_id.invoice_ids[0]
        invoice_id.signal_workflow("invoice_open")

        # Create the claim with a claim line
        claim_obj = self.env["crm.claim"]
        # Test code in customer claim
        claim_id = claim_obj.create({
            "name": "TEST CLAIM",
            "code": "/",
            "claim_type": claim_type_customer.id,
            "delivery_address_id": self.rma_customer_id.id,
            "partner_id": self.rma_customer_id.id,
            "invoice_id": invoice_id.id,
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
                "delivery_address_id": self.rma_customer_id.id,
                "partner_id": self.rma_customer_id.id,
                "invoice_id": invoice_id.id,
                "user_id": self.env.user.id
            })
        supplier_copy = claim_id.copy()
        self.assertTrue("RMA-V" in supplier_copy.code)
