# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2022 Tecnativa - Víctor Martínez
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
        order_line_obj = request.env["sale.order.line"]
        wizard_obj = request.env["sale.order.rma.wizard"].sudo()
        wizard_line_field_types = {
            f: d["type"] for f, d in wizard_obj.line_ids.fields_get().items()
        }
        # Set wizard line vals
        mapped_vals = {}
        custom_vals = {}
        partner_shipping_id = post.pop("partner_shipping_id", False)
        if partner_shipping_id:
            try:
                partner_shipping_id = int(partner_shipping_id)
            except ValueError:
                partner_shipping_id = False
        for name, value in post.items():
            try:
                row, field_name = name.split("-", 1)
                if wizard_line_field_types.get(field_name) == "many2one":
                    value = int(value) if value else False
                mapped_vals.setdefault(row, {}).update({field_name: value})
            # Catch possible form custom fields to add them to the RMA
            # description values
            except ValueError:
                custom_vals.update({name: value})
        for vals in mapped_vals.values():
            sale_line = order_line_obj.browse(vals.get("sale_line_id")).sudo()
            vals["allowed_quantity"] = sale_line.qty_delivered
        # If no operation is filled, no RMA will be created
        line_vals = [
            (0, 0, vals) for vals in mapped_vals.values() if vals.get("operation_id")
        ]
        # Create wizard an generate rmas
        order = order_obj.browse(order_id).sudo()
        location_id = order.warehouse_id.rma_loc_id.id
        # Add custom fields text
        custom_description = ""
        if custom_vals:
            custom_description = r"<br \>---<br \>"
            custom_description += r"<br \>".join(
                ["{}: {}".format(x, y) for x, y in custom_vals.items()]
            )
        wizard = wizard_obj.with_context(active_id=order_id).create(
            {
                "line_ids": line_vals,
                "location_id": location_id,
                "partner_shipping_id": partner_shipping_id,
                "custom_description": custom_description,
            }
        )
        user_has_group_portal = request.env.user.has_group(
            "base.group_portal"
        ) or request.env.user.has_group("base.group_public")
        rma = wizard.sudo().create_rma(from_portal=True)
        for rec in rma:
            rec.origin += _(" (Portal)")
        # Add the user as follower of the created RMAs so they can later view them.
        rma.message_subscribe([request.env.user.partner_id.id])
        # Subscribe the user to the notification subtype so he receives the confirmation
        # note.
        rma.message_follower_ids.filtered(
            lambda x: x.partner_id == request.env.user.partner_id
        ).subtype_ids += request.env.ref("rma.mt_rma_notification")
        if len(rma) == 0:
            route = order_sudo.get_portal_url()
        elif len(rma) == 1:
            route = rma._get_share_url() if user_has_group_portal else rma.access_url
        else:
            route = (
                order._get_share_url()
                if user_has_group_portal
                else "/my/rmas?sale_id=%d" % order_id
            )
        return request.redirect(route)

    @http.route(
        ["/my/requestrma/<int:order_id>"], type="http", auth="public", website=True
    )
    def request_sale_rma(self, order_id, access_token=None, **kw):
        """Request RMA on a single page"""
        try:
            order_sudo = self._document_check_access(
                "sale.order", order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        if order_sudo.state in ("draft", "sent", "cancel"):
            return request.redirect("/my")
        values = {
            "sale_order": order_sudo,
            "page_name": "request_rma",
            "default_url": order_sudo.get_portal_url(),
            "token": access_token,
            "partner_id": order_sudo.partner_id.id,
        }
        if order_sudo.company_id:
            values["res_company"] = order_sudo.company_id
        return request.render("rma_sale.request_rma_single_page", values)
