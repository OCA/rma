# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, HttpCase


class TestWebsiteRma(HttpCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {"name": "Website rma 1", "type": "product"}
        )
        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "outgoing"),
                "|",
                ("warehouse_id.company_id", "=", self.env.user.company_id.id),
                ("warehouse_id", "=", False),
            ],
            limit=1,
        )
        picking_form = Form(
            recordp=self.env["stock.picking"].with_context(
                default_picking_type_id=picking_type.id
            ),
            view="stock.view_picking_form",
        )
        picking_form.partner_id = self.env.user.partner_id
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product
            move.product_uom_qty = 10
        picking = picking_form.save()
        picking.action_confirm()
        picking.move_lines.quantity_done = 10
        picking.button_validate()

    def test_website_form_request_rma(self):
        self.start_tour("/my", "request_rma", login="admin")
        rma = self.env["rma"].search(
            [
                ("operation_id", "!=", False),
                ("description", "=", "RMA test from website form"),
            ]
        )
        self.assertTrue(bool(rma))
