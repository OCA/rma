# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestRmaBatchReasonCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reason = cls.env["rma.reason"].create(
            {
                "name": {"en_US": "Test Reason"},
            }
        )
        cls.other_reason = cls.env["rma.reason"].create(
            {
                "name": {"en_US": "Other Reason"},
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.operation = cls.env["rma.operation"].create(
            {
                "name": "Test RMA Operation",
            }
        )

    def _create_batch(self, reason=None):
        """Helper to create a batch with optional reason."""
        vals = {
            "partner_id": self.partner.id,
            "partner_shipping_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "company_id": self.env.company.id,
            "location_id": self.location.id,
            "operation_id": self.operation.id,
        }
        if reason:
            vals["reason_id"] = reason.id
        return self.env["rma.batch"].create(vals)

    def _create_rma(self, batch=None, reason=None, operation=None):
        """Helper to create an RMA with optional batch and reason.

        If operation or reason is given it will override the one from batch if any."""
        vals = {
            "partner_id": self.partner.id,
            "product_id": self.product.id,
            "product_uom_qty": 1.0,
        }
        if batch:
            vals["batch_id"] = batch.id
            if batch.operation_id:
                vals["operation_id"] = batch.operation_id.id
            if batch.reason_id:
                vals["reason_id"] = batch.reason_id.id
        if operation:
            vals["operation_id"] = operation.id
        if reason:
            vals["reason_id"] = reason.id
        return self.env["rma"].create(vals)
