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


class TestWarehouseByDefault(ClaimTestsCommon):

    def setUp(self):
        super(TestWarehouseByDefault, self).setUp()
        self.warehouse = self.env['stock.warehouse']

    def test_warehouse_by_default(self):
        """Check that the warehouse by default is correct
        """

        main_warehouse = self.env.ref("stock.warehouse0")

        user_warehouse = self.warehouse.create({
            "name": "User Warehouse",
            "code": "UWH"
        })

        company_warehouse = self.warehouse.create({
            "name": "Company Warehouse",
            "code": "CWH"
        })

        user = self.env.ref("crm_claim_rma.vendor_user_rma")
        sales_team = self.env.ref('sales_team.section_sales_department')
        sales_team.write({"default_warehouse": main_warehouse.id})
        self.env.user.write({'default_section_id': sales_team.id})

        claim_type = self.env.ref(
            "crm_claim_rma.crm_claim_type_customer")
        sale_id = self.create_sale_order(self.rma_customer_id)
        sale_id.signal_workflow('manual_invoice')
        self.assertTrue(sale_id.invoice_ids,
                        "The Order Sale of Agrolait not have Invoice")
        invoice_id = sale_id.invoice_ids[0]
        invoice_id.signal_workflow("invoice_open")

        # Create the claim with a claim line
        data = {
            "name": "TEST CLAIM",
            "code": "/",
            "claim_type": claim_type.id,
            "delivery_address_id": self.rma_customer_id.id,
            "partner_id": self.rma_customer_id.id,
            "invoice_id": invoice_id.id,
            "user_id": user.id
        }
        claim_obj = self.env["crm.claim"]
        claim_id = claim_obj.create(data)
        claim_id.with_context({"create_lines": True}).\
            _onchange_invoice_warehouse_type_date()

        # take the first warehouse of claim.user_id.company
        self.assertEquals(claim_id.warehouse_id, main_warehouse)

        # take the warehouse of claim company claim.company_id.rma_warehouse_id
        sales_team.write({"default_warehouse": company_warehouse.id})
        data['code'] = '/'
        claim_id = claim_obj.create(data)
        self.assertEquals(claim_id.warehouse_id, company_warehouse)

        # take the warehouse of claim user claim.user_id.rma_warehouse_id
        sales_team.write({"default_warehouse": user_warehouse.id})
        data['code'] = '/'
        claim_id = claim_obj.create(data)
        self.assertEquals(claim_id.warehouse_id, user_warehouse)

        # Delete all warehouse available to main_company
        sales_team.write({"default_warehouse": False})
        data['code'] = '/'
        claim_id = claim_obj.create(data)
        self.assertEquals(claim_id.warehouse_id,
                          self.env.ref("stock.warehouse0"))
