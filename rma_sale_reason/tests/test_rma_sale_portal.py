# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.rma_sale.tests.test_rma_sale_portal import (
    TestRmaSalePortal as TestRmaSalePortalBase,
)


@tagged("-at-install", "post-install")
class TestRmaSalePortal(TestRmaSalePortalBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rma_reason = cls.env["rma.reason"].create({"name": "Reason"})

    def test_rma_sale_reason_portal(self):
        self.start_tour("/", "rma_sale_reason_portal", login="rma_portal")
        rma = self.sale_order.rma_ids
        # Check that the portal values are properly transmited
        self.assertEqual(rma.reason_id, self.rma_reason)
