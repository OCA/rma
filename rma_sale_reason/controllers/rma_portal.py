# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http

from odoo.addons.rma_sale.controllers.sale_portal import CustomerPortal


class RmaPortal(CustomerPortal):
    @http.route(
        ["/my/orders/<int:order_id>/requestrma"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def request_rma(self, order_id, access_token=None, **post):
        """
        We used a hidden input to determine whether the reason is required or not.
        Now, we remove it from the post data as the base controller puts all custom
        inputs in the description field.
        """
        if "is_rma_reason_required" in post:
            del post["is_rma_reason_required"]
        return super().request_rma(order_id, access_token=access_token, **post)
