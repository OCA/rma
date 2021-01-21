# Copyright 2021 Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestPurchaseRequisitionReport(TransactionCase):
    def setUp(self):
        super(TestPurchaseRequisitionReport, self).setUp()
        self.base_comment_model = self.env["base.comment.template"]
        self.before_comment = self._create_comment("before_lines")
        self.after_comment = self._create_comment("after_lines")
        self.partner_id = self.env["res.partner"].create({"name": "Partner Test"})
        self.product = self.env.ref("product.product_product_3")
        self.location = self.env.ref("stock.stock_location_stock")
        self.repair = self.env.ref("repair.repair_r1")
        self.repair.update(
            {
                "comment_template1_id": self.before_comment.id,
                "comment_template2_id": self.after_comment.id,
            }
        )
        self.repair._set_note1()
        self.repair._set_note2()

    def _create_comment(self, position):
        return self.base_comment_model.create(
            {
                "name": "Comment " + position,
                "position": position,
                "text": "Text " + position,
            }
        )

    def test_comments_in_repair(self):
        res = (
            self.env["ir.actions.report"]
            ._get_report_from_name("repair.report_repairorder2")
            ._render_qweb_html(self.repair.ids)
        )
        self.assertRegex(str(res[0]), self.before_comment.text)
        self.assertRegex(str(res[0]), self.after_comment.text)

    def test_onchange_partner_id(self):
        self.partner_id.property_comment_template_id = self.after_comment.id
        vals = {
            "partner_id": self.partner_id.id,
            "product_id": self.product.id,
            "product_uom": self.product.uom_id.id,
            "location_id": self.location.id,
        }
        new_repair = self.env["repair.order"].new(vals)
        new_repair.onchange_partner_id_comment()
        purchase_dict = new_repair._convert_to_write(new_repair._cache)
        new_repair = self.env["repair.order"].create(purchase_dict)
        self.assertEqual(new_repair.comment_template2_id, self.after_comment)
        self.partner_id.property_comment_template_id = self.before_comment.id
        new_repair = self.env["repair.order"].new(vals)
        new_repair.onchange_partner_id_comment()
        purchase_dict = new_repair._convert_to_write(new_repair._cache)
        new_repair = self.env["repair.order"].create(purchase_dict)
        self.assertEqual(new_repair.comment_template1_id, self.before_comment)
