# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import Command
from odoo.tests import HttpCase, tagged

from .test_rma_sale import TestRmaSaleBase


@tagged("-at-install", "post-install")
class TestRmaSalePortal(TestRmaSaleBase, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls._create_sale_order(cls, [[cls.product_1, 5]])
        # So we can click it in the tour
        cls.sale_order.name = "Test Sale RMA SO"
        cls.sale_order.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda r: r.product_id == cls.product_1
        )
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity_done = 5
        cls.order_out_picking.button_validate()
        # Let's create some companion contacts
        cls.partner_company = cls.res_partner.create(
            {"name": "Partner test Co", "email": "partner_co@test.com"}
        )
        cls.another_partner = cls.res_partner.create(
            {
                "name": "Another address",
                "email": "another_partner@test.com",
                "parent_id": cls.partner_company.id,
            }
        )
        cls.partner.parent_id = cls.partner_company
        # Create our portal user
        cls.user_portal = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "rma_portal",
                    "password": "rma_portal",
                    "partner_id": cls.partner.id,
                    "groups_id": [Command.set([cls.env.ref("base.group_portal").id])],
                }
            )
        )

    def test_rma_sale_portal(self):
        self.start_tour("/", "rma_sale_portal", login="rma_portal")
        rma = self.sale_order.rma_ids
        # Check that the portal values are properly transmited
        self.assertEqual(rma.state, "draft")
        self.assertEqual(rma.partner_id, self.partner)
        self.assertEqual(rma.partner_shipping_id, self.another_partner)
        self.assertEqual(rma.product_uom_qty, 1)
        self.assertEqual(
            rma.description, Markup("<p>I'd like to change this product</p>")
        )
