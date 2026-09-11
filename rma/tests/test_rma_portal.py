# Copyright 2026 Studio73 - Eugenio Micó <eugenio@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers.main import PortalRma


@tagged("-at_install", "post_install")
class TestRmaPortal(BaseCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        warehouse = cls.env.ref("stock.warehouse0")
        partner = cls.env["res.partner"].create(
            {"name": "RMA portal customer", "email": "rma-portal@example.com"}
        )
        product = cls.env["product.product"].create(
            {"name": "RMA portal product", "is_storable": True}
        )
        operation = cls.env["rma.operation"].create(
            {
                "name": "RMA portal operation",
                "action_create_receipt": "automatic_on_confirm",
                "action_create_delivery": "automatic_on_confirm",
            }
        )
        cls.rma = cls.env["rma"].create(
            {
                "partner_id": partner.id,
                "partner_shipping_id": partner.id,
                "partner_invoice_id": partner.id,
                "product_id": product.id,
                "product_uom_qty": 1,
                "location_id": warehouse.rma_loc_id.id,
                "operation_id": operation.id,
            }
        )
        cls.rma.action_confirm()
        cls.portal_user = new_test_user(
            cls.env,
            login="rma_portal",
            password="rma_portal",
            groups="base.group_portal",
            partner_id=partner.id,
        )
        cls.internal_user = new_test_user(
            cls.env,
            login="rma_internal",
            password="rma_internal",
            groups="rma.rma_group_manager,stock.group_stock_manager",
        )
        cls.rma_only_user = new_test_user(
            cls.env,
            login="rma_only",
            password="rma_only",
            groups="rma.rma_group_user_all",
        )
        cls.portal_url = cls.rma.get_portal_url()
        cls.access_token = cls.rma.access_token

    def test_portal_picking_dates(self):
        response = self.url_open(self.portal_url)
        self.assertEqual(response.status_code, 200)

        pickings = (
            self.rma.reception_move_id.picking_id
            | self.rma.delivery_move_ids.picking_id
        )
        for picking in pickings:
            picking.move_ids.quantity = picking.move_ids.product_uom_qty
            picking.button_validate()
        self.assertEqual(set(pickings.mapped("state")), {"done"})
        self.assertTrue(all(pickings.mapped("date_done")))

        response = self.url_open(self.portal_url)
        self.assertEqual(response.status_code, 200)

    def test_portal_home_and_rma_list(self):
        self.authenticate("rma_portal", "rma_portal")
        response = self.url_open("/my")
        self.assertEqual(response.status_code, 200)
        response = self.url_open("/my/rmas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.rma.name, response.text)

        response = self.url_open(
            "/my/rmas?sortby=state&date_begin=2000-01-01&date_end=2100-01-01"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.rma.name, response.text)

    def test_portal_home_counter_values(self):
        controller = PortalRma()
        with MockRequest(self.env):
            values = controller._prepare_home_portal_values({"rma_count"})
        self.assertEqual(values["rma_count"], self.env["rma"].search_count([]))

        rma_model_class = type(self.env["rma"])
        with patch.object(rma_model_class, "has_access", return_value=False):
            with MockRequest(self.env):
                values = controller._prepare_home_portal_values({"rma_count"})
        self.assertEqual(values["rma_count"], 0)

    def test_portal_without_rma_access(self):
        rma_model_class = type(self.env["rma"])
        with patch.object(rma_model_class, "has_access", return_value=False):
            self.authenticate("rma_portal", "rma_portal")
            response = self.url_open("/my")
            self.assertEqual(response.status_code, 200)
            response = self.url_open("/my/rmas", allow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertTrue(response.headers["Location"].endswith("/my"))

    def test_portal_rma_detail_reports_and_missing_record(self):
        response = self.url_open(f"{self.portal_url}&report_type=html")
        self.assertEqual(response.status_code, 200)

        response = self.url_open("/my/rmas/0", allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["Location"].endswith("/my"))

    def test_portal_picking_report_access(self):
        picking = self.rma.reception_move_id.picking_id
        report_url = f"/my/rma/picking/pdf/{self.rma.id}/{picking.id}"

        response = self.url_open(
            f"{report_url}?access_token=invalid", allow_redirects=False
        )
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["Location"].endswith("/my"))

        self.authenticate("rma_portal", "rma_portal")
        response = self.url_open(
            f"{report_url}?access_token={self.access_token}",
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertTrue(response.content)

        self.authenticate("rma_internal", "rma_internal")
        response = self.url_open(report_url)
        self.assertEqual(response.status_code, 200)

    def test_picking_access_token_checks(self):
        controller = PortalRma()
        picking = self.rma.reception_move_id.picking_id
        rma_only_env = self.env(user=self.rma_only_user)
        with MockRequest(rma_only_env):
            self.assertEqual(
                controller._picking_check_access(
                    self.rma.id, picking.id, self.access_token
                ),
                picking,
            )
            with self.assertRaises(AccessError):
                controller._picking_check_access(self.rma.id, picking.id, "invalid")
