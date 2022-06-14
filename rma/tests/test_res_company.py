from odoo.tests import tagged

from odoo.addons.rma.tests.test_rma import TestRma


@tagged("current")
class TestRmaHooks(TestRma):
    def test_default_rma_mail_confirmation_template(self):
        result = self.company._default_rma_mail_confirmation_template()
        self.assertEqual(result, self.env.ref("rma.mail_template_rma_notification").id)

        result = self.company._default_rma_mail_receipt_template()
        self.assertEqual(
            result, self.env.ref("rma.mail_template_rma_receipt_notification").id
        )

        result = self.company._default_rma_mail_draft_template()
        self.assertEqual(
            result, self.env.ref("rma.mail_template_rma_draft_notification").id
        )

        new_company = self.env["res.company"].create({"name": "New Company"})

        new_rma_indexes = self.env["ir.sequence"].search(
            [("company_id", "=", new_company.id), ("code", "=", "rma")]
        )

        self.assertEqual(new_rma_indexes.name, "RMA Code")
