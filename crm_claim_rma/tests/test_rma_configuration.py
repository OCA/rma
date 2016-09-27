# coding: utf-8
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://www.vauxoo.com>).
#    All Rights Reserved
# ############ Credits ########################################################
#    Coded by: Yanina Aular <yani@vauxoo.com>
#    Planified by: Yanina Aular <yani@vauxoo.com>
#    Audited by: Nhomar Hernandez <nhomar@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import datetime
from openerp.exceptions import ValidationError
from .common import ClaimTestsCommon


class TestCreateSimpleClaim(ClaimTestsCommon):

    def setUp(self):
        super(TestCreateSimpleClaim, self).setUp()
        self.company = self.env.ref("base.main_company")

    def test_rma_cofiguration(self):
        # Main Company Configuration

        self.company.write({
            "limit_days": 10,
            "priority_maximum": 7,
            "priority_minimum": 14,
        })

        # check the data of the company will be
        # the correct data on the wizard of rma settings
        rma_config = self.env["rma.config.settings"]
        data = rma_config.get_default_rma_values()
        self.assertEqual(data.get("limit_days"), 10)
        self.assertEqual(data.get("priority_maximum"), 7)
        self.assertEqual(data.get("priority_minimum"), 14)

        # set the data on the rma settings wizard
        new_data = {
            "limit_days": 20,
            "priority_maximum": 9,
            "priority_minimum": 16,
        }
        rma_config_brw = rma_config.create(new_data)
        rma_config_brw.execute()

        # verify the new data sets on the wizard in the company
        self.assertEqual(self.company.limit_days, 20)
        self.assertEqual(self.company.priority_maximum, 9)
        self.assertEqual(self.company.priority_minimum, 16)

        data = rma_config.get_default_rma_values()
        data.update({
            "priority_maximum": 18,
            "priority_minimum": 16,
        })
        error = ("Priority maximum must be less than priority_minimum")
        with self.assertRaisesRegexp(ValidationError, error):
            rma_config_brw = rma_config.create(data)

        data = rma_config.get_default_rma_values()
        data.update({
            "priority_maximum": 0,
            "priority_minimum": 16,
        })
        error = ("Priority maximum and priority_minimum must "
                 "be greater than zero")
        with self.assertRaisesRegexp(ValidationError, error):
            rma_config_brw = rma_config.create(data)

        error = "Limit days must be greater than zero"
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({
                "limit_days": 0,
            })

    def test_limit_days(self):
        # Main Company Configuration
        self.company.write({
            "limit_days": 10,
        })

        # User Administrator
        user = self.env.ref("base.user_root")

        # Company's user administrator
        user.write({"company_id": self.company.id})

        # Create claim
        claim_id = self.env["crm.claim"].create({
            "name": "TEST SIMPLE CLAIM",
            "claim_type": self.customer_type.id,
            "partner_id": self.rma_customer_id.id,
            "pick": True,
            "user_id": user.id,
            "date": "2016-12-01 00:00:00",
        })

        # Test 1
        self.assertEqual(claim_id.date_deadline, "2016-12-11")

        # Test 2
        claim_id.write({"date": "2016-12-10 00:00:00"})
        self.assertEqual(claim_id.date_deadline, "2016-12-20")

        # Test 3
        error = "Creation date must be less than deadline"
        with self.assertRaisesRegexp(ValidationError, error):
            claim_id.write({"date_deadline": "2016-12-01"})

        user_rma = self.env.ref("crm_claim_rma.vendor_user_rma")
        error = "In order to set a manual deadline date.*"
        with self.assertRaisesRegexp(ValidationError, error):
            claim_id.sudo(user_rma).write({"date_deadline": "2016-12-22"})

        # Test 4
        error = "Creation date must be less than deadline"
        with self.assertRaisesRegexp(ValidationError, error):
            claim_id.write({"date_deadline": "2016-12-09"})

        # Test 5
        error = "Limit days must be greater than zero"
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({"limit_days": -1})

        # Test 6
        error = "Limit days must be greater than zero"
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({"limit_days": 0})

    def test_priority(self):

        # Main Company Configuration
        self.company.write({
            "priority_maximum": 1,
            "priority_minimum": 7,
        })

        crm_claim = self.env.ref("crm_claim.crm_claim_6")
        claim_line_1 = crm_claim.claim_line_ids[0]

        # Sale Invoice
        invoice = claim_line_1.invoice_line_id.invoice_id

        today = datetime.datetime.now()
        datetime_format = "%Y-%m-%d %H:%M:%S"

        # Test 1
        date_invoice = datetime.datetime.strftime(today, datetime_format)
        invoice.write({"date_invoice": date_invoice})
        self.assertEqual(claim_line_1.priority, "3_very_high")

        # Test 2
        date_invoice = today - datetime.timedelta(days=4)
        date_invoice = datetime.datetime.strftime(
            date_invoice, datetime_format)
        invoice.write({"date_invoice": date_invoice})
        crm_claim.write({"date": date_invoice})
        claim_line_1.refresh()
        claim_line_1._compute_priority()
        self.assertEqual(claim_line_1.priority, "2_high")

        # Test 3
        date_invoice = today - datetime.timedelta(days=9)
        date_invoice = datetime.datetime.strftime(
            date_invoice, datetime_format)
        invoice.write({"date_invoice": date_invoice})
        claim_line_1.refresh()
        claim_line_1._compute_priority()
        self.assertEqual(claim_line_1.priority, "1_normal")

        # Test 4
        invoice.write({"date_invoice": False})
        claim_line_1.refresh()
        claim_line_1._compute_priority()
        self.assertEqual(claim_line_1.priority, "0_not_define")

        # Test 5
        error = ("Priority maximum and priority_minimum must "
                 "be greater than zero")
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({"priority_maximum": 0})

        # Test 6
        error = ("Priority maximum and priority_minimum must "
                 "be greater than zero")
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({"priority_maximum": -1})

        # Test 7
        error = ("Priority maximum must be less than priority_minimum")
        with self.assertRaisesRegexp(ValidationError, error):
            self.company.write({"priority_maximum": 8})
