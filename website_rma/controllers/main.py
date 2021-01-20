# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from odoo import http
from odoo.http import request

from odoo.addons.website_form.controllers.main import WebsiteForm


class WebsiteForm(WebsiteForm):
    def insert_record(self, request, model, values, custom, meta=None):
        res = super().insert_record(request, model, values, custom, meta)
        # Add the customer to the followers, the same as when creating
        # an RMA from a sales order in the portal.
        if model.model == "rma":
            rma = request.env["rma"].sudo().browse(res)
            rma.message_subscribe([rma.partner_id.id])
        return res


class WebsiteRMA(http.Controller):
    def _get_website_rma_product_domain(self, q):
        """Domain used for the products to be shown in selection of
        the web form.
        """
        domain = [
            ("name", "=ilike", "%{}%".format(q or "")),
            ("sale_ok", "=", True),
        ]
        # HACK: As there is no glue module for this purpose we have put
        # this this condition to check that the mrp module is installed.
        if "bom_ids" in request.env["product.product"]._fields:
            domain += [
                "|",
                ("bom_ids.type", "!=", "phantom"),
                ("bom_ids", "=", False),
            ]
        return domain

    @http.route(["/requestrma"], type="http", auth="user", website=True)
    def request_rma(self, **kw):
        return http.request.render("website_rma.request_rma", {})

    @http.route(
        "/website_rma/get_products",
        type="http",
        auth="user",
        methods=["GET"],
        website=True,
    )
    def rma_product_read(self, q="", limit=25, **post):
        data = (
            request.env["product.product"]
            .sudo()
            .search_read(
                domain=self._get_website_rma_product_domain(q),
                fields=["id", "display_name", "uom_id"],
                limit=int(limit),
            )
        )
        return json.dumps(data)
