# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.fields import Date as FieldsDate
from odoo.tests import common, tagged

from odoo.addons.rma.controllers.main import PortalRma
from odoo.addons.rma.tests.test_rma import TestRma
from odoo.addons.website.tools import MockRequest


class TestRmaCont(TestRma, common.HttpCase):
    def setUp(self):
        # super(TestRmaCont, self).setUpClass()
        super(TestRmaCont, self).setUp()

        self.public_user = self.env.ref("base.public_user")
        self.user_admin = self.env.ref("base.user_admin")
        self.model_partner = self.env.ref("base.model_res_partner")


@tagged("current")
class TestRmaContPortal(TestRmaCont):
    def test_prepare_portal_layout_values(self):

        with MockRequest(self.env):
            values = PortalRma()._prepare_portal_layout_values()
            self.assertEqual(values["page_name"], "home")

        with MockRequest(self.env):

            rma = self._create_rma(self.partner, self.product, 10, self.rma_loc)

            values = PortalRma()._rma_get_page_view_values(rma, rma.access_token)
            self.assertEqual(values, {"page_name": "RMA", "rma": rma})

        with MockRequest(self.env):
            kw = {}
            values = PortalRma()._get_filter_domain(kw)
            self.assertEqual(values, [])

        with MockRequest(self.env):
            values = PortalRma().portal_my_rmas()
            self.assertEqual(values.called, False)

    def test_SO_and_DO_portal_acess(self):

        # self.authenticate(self.user.login, self.user_password)
        self.authenticate("admin", "admin")
        date_begin = FieldsDate.to_string(datetime.today() + timedelta(days=1))
        date_end = FieldsDate.to_string(datetime.today() + timedelta(days=1))
        url = f"/my/rmas?date_begin={date_begin}&date_end={date_end}"
        response = self.url_open(
            url=url,
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_id(self):
        self.authenticate("admin", "admin")
        unknown_id = 1
        url = f"/my/rmas/{unknown_id}"

        response = self.url_open(
            url=url,
            allow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)

    def test_portal_my_rma_detail(self):
        # result = self.authenticate("admin", "admin")
        rma_1 = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        # self.authenticate("portal", "portal")
        self.authenticate("admin", "admin")
        report_type = "html"
        url = f"/my/rmas/{rma_1.id}?report_type={report_type}"

        response = self.url_open(
            url=url,
            allow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)

        url = f"/my/rmas/{rma_1.id}"

        response = self.url_open(
            url=url,
            allow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)

    def test_portal_my_rma_picking_report(self):

        rma_1 = self._create_rma(self.partner, self.product, 10, self.rma_loc)
        rma_1.action_confirm()

        url = f"/my/rma/picking/pdf/{rma_1.id}/{rma_1.reception_move_id.picking_id.id}"
        response = self.url_open(
            url=url,
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.authenticate("admin", "admin")
        response = self.url_open(
            url=url,
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
