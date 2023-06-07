# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @http.route(
        ["/my/orders/<int:order_id>/requestrma"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def request_rma(self, order_id, access_token=None, **post):
        try:
            order_sudo = self._document_check_access(
                "sale.order", order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        order_obj = request.env["sale.order"]
        wizard_obj = request.env["sale.order.rma.wizard"]
        # Set wizard line vals
        mapped_vals = {}
        for name, value in post.items():
            row, field_name = name.split("-", 1)
            mapped_vals.setdefault(row, {}).update({field_name: value})
        # If no operation is filled, no RMA will be created
        line_vals = [
            (0, 0, vals) for vals in mapped_vals.values() if vals.get("operation_id")
        ]
        # Create wizard an generate rmas
        order = order_obj.browse(order_id).sudo()
        location_id = order.warehouse_id.rma_loc_id.id
        wizard = wizard_obj.with_context(active_id=order_id).create(
            {"line_ids": line_vals, "location_id": location_id}
        )
        rma = wizard.sudo().create_rma()
        for rec in rma:
            rec.origin += _(" (Portal)")
        # Add the user as follower of the created RMAs so they can
        # later view them.
        rma.message_subscribe([request.env.user.partner_id.id])
        if len(rma) == 0:
            route = order_sudo.get_portal_url()
        else:
            route = "/my/rmas?sale_id=%d" % order_id
        return request.redirect(route)
