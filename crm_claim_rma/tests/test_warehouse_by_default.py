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

from openerp.exceptions import Warning as UserError
from openerp.tests import common


class TestWarehouseByDefault(common.TransactionCase):

    def setUp(self):
        super(TestWarehouseByDefault, self).setUp()
        self.warehouse = self.env['stock.warehouse']

    def test_warehouse_by_default(self):
        """ Check that the warehouse by default is correct
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
        company = user.company_id
        user.write({"rma_warehouse_id": False})
        company.write({"rma_warehouse_id": False})

        partner = self.env.ref("base.res_partner_2")
        partner_address = self.env.ref("base.res_partner_12")
        claim_type = self.env.ref(
            "crm_claim_rma.crm_claim_type_customer")
        sale_order_agrolait_demo = self.env.ref("sale.sale_order_1")
        self.assertTrue(
            sale_order_agrolait_demo.invoice_ids,
            "The Order Sale of Agrolait not have Invoice")
        invoice_agrolait = sale_order_agrolait_demo.invoice_ids[0]
        invoice_agrolait.signal_workflow("invoice_open")

        # Create the claim with a claim line
        claim_obj = self.env["crm.claim"]
        claim_id = claim_obj.create(
            {
                "name": "TEST CLAIM",
                "code": "/",
                "claim_type": claim_type.id,
                "delivery_address_id": partner_address.id,
                "partner_id": partner.id,
                "invoice_id": invoice_agrolait.id,
                "user_id": user.id
            })
        claim_id.with_context({"create_lines": True}).\
            _onchange_invoice_warehouse_type_date()

        # take the first warehouse of claim.user_id.company
        self.assertEquals(claim_id.warehouse_id,
                          main_warehouse)

        # take the warehouse of claim company claim.company_id.rma_warehouse_id
        company.write({"rma_warehouse_id": company_warehouse.id})
        claim_id._onchange_default_warehouse()
        self.assertEquals(claim_id.warehouse_id,
                          company_warehouse)

        # take the warehouse of claim user claim.user_id.rma_warehouse_id
        user.write({"rma_warehouse_id": user_warehouse.id})
        claim_id._onchange_default_warehouse()
        self.assertEquals(claim_id.warehouse_id,
                          user_warehouse)

        # Delete all warehouse available to main_company
        company_obj = self.env["res.company"]
        company_test = company_obj.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "parent_id": self.env.ref("base.main_company").id,
                "currency_id": self.env.ref("base.EUR").id,
                "name": "Company Test",
            }
        )

        wh_obj = self.env["stock.warehouse"]
        wh_obj.search([]).write({"company_id": company_test.id})
        user.write({"rma_warehouse_id": False})
        company.write({"rma_warehouse_id": False})
        error = "There is no warehouse for the current user's company"
        with self.assertRaisesRegexp(UserError, error):
            claim_id._onchange_default_warehouse()
