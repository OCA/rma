# Copyright 2026 Studio73 - Eugenio Micó <eugenio@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import Mock, patch

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form

from odoo.addons.rma_sale.controllers.rma_portal import PortalRma
from odoo.addons.rma_sale.controllers.sale_portal import CustomerPortal

from .test_rma_sale import TestRmaSaleBase


class TestRmaSaleCoverage(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls._create_sale_order(
            [[cls.product_1, 5], [cls.product_2, 5]]
        )
        cls.sale_order.action_confirm()
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity = 5
        cls.order_out_picking.button_validate()
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda line: line.product_id == cls.product_1
        )

    def test_sale_order_actions_and_line_data(self):
        draft_order = self._create_sale_order([[self.product_1, 1]])
        with self.assertRaisesRegex(
            ValidationError, "You may only create RMAs from a confirmed sale order."
        ):
            draft_order.action_create_rma()

        empty_action = self.sale_order.action_view_rma()
        self.assertEqual(empty_action["domain"], [("id", "in", [])])
        self.assertEqual(empty_action["context"], {})

        wizard = self._rma_sale_wizard(self.sale_order)
        wizard.line_ids.filtered(
            lambda line: line.product_id == self.product_2
        ).quantity = 0
        rma = wizard.create_rma()
        single_action = self.sale_order.action_view_rma()
        self.assertEqual(single_action["res_id"], rma.id)
        self.assertEqual(single_action["view_mode"], "form")
        self.assertEqual(single_action["context"], {})

        wizard = self._rma_sale_wizard(self.sale_order)
        wizard.line_ids.filtered(
            lambda line: line.product_id == self.product_1
        ).quantity = 0
        wizard.create_rma()
        multiple_action = self.sale_order.action_view_rma()
        self.assertEqual(
            multiple_action["domain"],
            [("id", "in", self.sale_order.rma_ids.ids)],
        )
        self.assertEqual(multiple_action["context"], {})

    def test_sale_order_line_without_delivery_or_stock_product(self):
        service = self.product_product.create(
            {"name": "Service test", "type": "service"}
        )
        service_order = self._create_sale_order([[service, 1]])
        self.assertEqual(service_order.order_line.prepare_sale_rma_data(), {})
        self.assertEqual(service_order.get_delivery_rma_data(), [])

        undelivered_order = self._create_sale_order([[self.product_1, 1]])
        undelivered_order.action_confirm()
        data = undelivered_order.order_line.prepare_sale_rma_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product"], self.product_1)
        self.assertEqual(data[0]["quantity"], 0)
        self.assertFalse(data[0]["picking"])

    def test_sale_order_rma_wizard_computes_and_empty_result(self):
        wizard = self._rma_sale_wizard(self.sale_order)
        line = wizard.line_ids.filtered(lambda line: line.product_id == self.product_1)
        line.picking_id = self.order_out_picking
        line.onchange_product_id()
        self.assertFalse(line.picking_id)
        self.assertEqual(line.uom_id, self.product_1.uom_id)

        line._compute_allowed_product_ids()
        self.assertEqual(line.allowed_product_ids, self.product_1 | self.product_2)
        line._compute_allowed_picking_ids()
        self.assertEqual(line.allowed_picking_ids, self.order_out_picking)

        wizard.is_return_all = False
        self.assertFalse(wizard.line_ids.filtered(lambda record: record.quantity))
        self.assertIsNone(wizard.create_and_open_rma())

    def test_replace_procurement_keeps_sale_line(self):
        self.operation.action_create_refund = "update_quantity"
        wizard = self._rma_sale_wizard(self.sale_order)
        wizard.line_ids.filtered(
            lambda line: line.product_id == self.product_2
        ).quantity = 0
        rma = wizard.create_rma()
        vals = rma._prepare_replace_procurement_vals()
        self.assertEqual(vals["sale_line_id"], self.order_line.id)

    def test_return_picking_sale_links(self):
        return_wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=self.order_out_picking.ids,
                active_id=self.order_out_picking.id,
                active_model="stock.picking",
            )
        ).save()
        self.assertEqual(
            return_wizard._prepare_rma_partner_values(),
            (
                self.sale_order.partner_id,
                self.sale_order.partner_invoice_id,
                self.sale_order.partner_shipping_id,
            ),
        )
        self.assertEqual(
            return_wizard._prepare_rma_vals()["order_id"], self.sale_order.id
        )

        delivery = self._create_delivery()
        return_wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=delivery.ids,
                active_id=delivery.id,
                active_model="stock.picking",
            )
        ).save()
        partner_values = return_wizard._prepare_rma_partner_values()
        self.assertEqual(partner_values[0], self.partner)
        self.assertNotIn("order_id", return_wizard._prepare_rma_vals())

    def test_rma_portal_filter_domain(self):
        domain = PortalRma()._get_filter_domain({"sale_id": str(self.sale_order.id)})
        self.assertIn(("order_id", "=", self.sale_order.id), domain)

    def test_sale_order_invoiced_with_rma_refund(self):
        wizard = self._rma_sale_wizard(self.sale_order)
        wizard.line_ids.filtered(
            lambda line: line.product_id == self.product_2
        ).quantity = 0
        rma = wizard.create_rma()
        refund = self.env["account.move"].create(
            {
                "move_type": "out_refund",
                "partner_id": self.sale_order.partner_id.id,
                "journal_id": self.sale_journal.id,
            }
        )
        rma.refund_id = refund
        self.sale_order._get_invoiced()
        self.assertIn(refund, self.sale_order.invoice_ids)


class TestRmaSalePortalController(TestRmaSaleBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls._create_sale_order([[cls.product_1, 5]])
        cls.sale_order.action_confirm()
        cls.order_out_picking = cls.sale_order.picking_ids
        cls.order_out_picking.move_ids.quantity = 5
        cls.order_out_picking.button_validate()
        cls.order_line = cls.sale_order.order_line.filtered(
            lambda line: line.product_id == cls.product_1
        )

    def _request(self, env=None):
        request = Mock()
        request.env = env or self.env
        request.redirect.return_value = "redirected"
        request.render.return_value = "rendered"
        return request

    def test_request_sale_rma(self):
        portal = CustomerPortal()
        request = self._request()
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal, "_document_check_access", return_value=self.sale_order
            ),
        ):
            result = portal.request_sale_rma(
                self.sale_order.id, access_token="access-token"
            )
        self.assertEqual(result.get_data(as_text=True), "rendered")
        values = request.render.call_args.args[1]
        self.assertEqual(values["sale_order"], self.sale_order)
        self.assertEqual(values["token"], "access-token")

        request = self._request()
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal,
                "_document_check_access",
                side_effect=AccessError("not allowed"),
            ),
        ):
            result = portal.request_sale_rma(self.sale_order.id)
            self.assertEqual(result.get_data(as_text=True), "redirected")

        draft_order = self._create_sale_order([[self.product_1, 1]])
        request = self._request()
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(portal, "_document_check_access", return_value=draft_order),
        ):
            result = portal.request_sale_rma(draft_order.id)
            self.assertEqual(result.get_data(as_text=True), "redirected")

    def test_request_rma(self):
        portal = CustomerPortal()
        request = self._request()
        post = {
            "partner_shipping_id": str(self.partner_shipping.id),
            "line-sale_line_id": str(self.order_line.id),
            "line-product_id": str(self.product_1.id),
            "line-quantity": "1",
            "line-uom_id": str(self.order_line.product_uom_id.id),
            "line-picking_id": str(self.order_out_picking.id),
            "line-operation_id": str(self.operation.id),
            "damage_reason": "Damaged",
        }
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal, "_document_check_access", return_value=self.sale_order
            ),
        ):
            result = portal.request_rma(self.sale_order.id, **post)
        self.assertEqual(result.get_data(as_text=True), "redirected")
        request.redirect.assert_called_once()
        rma = self.env["rma"].search(
            [("order_id", "=", self.sale_order.id)], order="id desc", limit=1
        )
        self.assertIn("Damaged", rma.description)

        request = self._request()
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal,
                "_document_check_access",
                side_effect=AccessError("not allowed"),
            ),
        ):
            result = portal.request_rma(self.sale_order.id)
        self.assertEqual(result.get_data(as_text=True), "redirected")

        request = self._request()
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal, "_document_check_access", return_value=self.sale_order
            ),
        ):
            result = portal.request_rma(
                self.sale_order.id,
                partner_shipping_id="not-an-id",
                custom_field="No operation",
            )
        self.assertEqual(result.get_data(as_text=True), "redirected")

        request = self._request()
        multiple_post = {
            "partner_shipping_id": str(self.partner_shipping.id),
            "first-sale_line_id": str(self.order_line.id),
            "first-product_id": str(self.product_1.id),
            "first-quantity": "1",
            "first-uom_id": str(self.order_line.product_uom_id.id),
            "first-picking_id": str(self.order_out_picking.id),
            "first-operation_id": str(self.operation.id),
            "second-sale_line_id": str(self.order_line.id),
            "second-product_id": str(self.product_1.id),
            "second-quantity": "1",
            "second-uom_id": str(self.order_line.product_uom_id.id),
            "second-picking_id": str(self.order_out_picking.id),
            "second-operation_id": str(self.operation.id),
        }
        with (
            patch("odoo.addons.rma_sale.controllers.sale_portal.request", request),
            patch.object(
                portal, "_document_check_access", return_value=self.sale_order
            ),
        ):
            result = portal.request_rma(self.sale_order.id, **multiple_post)
        self.assertEqual(result.get_data(as_text=True), "redirected")
        self.assertEqual(
            request.redirect.call_args.args[0],
            f"/my/rmas?sale_id={self.sale_order.id}",
        )
