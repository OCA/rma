# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    # RMAs that were created from the delivery move
    rma_ids = fields.One2many(
        comodel_name="rma",
        inverse_name="move_id",
        string="RMAs",
        copy=False,
    )
    # RMAs linked to the incoming movement from client
    rma_receiver_ids = fields.One2many(
        comodel_name="rma",
        inverse_name="reception_move_id",
        string="RMA receivers",
        copy=False,
    )
    # RMA that create the delivery movement to the customer
    rma_id = fields.Many2one(
        comodel_name="rma",
        string="RMA return",
        copy=False,
    )

    def unlink(self):
        # A stock user could have no RMA permissions, so the ids wouldn't
        # be accessible due to record rules.
        rma_receiver = self.sudo().mapped("rma_receiver_ids")
        rma = self.sudo().mapped("rma_id")
        res = super().unlink()
        rma_receiver.filtered(lambda x: x.state != "cancelled").write(
            {"state": "draft"}
        )
        rma.update_received_state()
        rma.update_replaced_state()
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        # A stock user could have no RMA permissions, so the ids wouldn't
        # be accessible due to record rules.
        cancelled_moves = self.filtered(lambda r: r.state == "cancel").sudo()
        cancelled_moves.mapped("rma_receiver_ids").write({"state": "draft"})
        cancelled_moves.mapped("rma_id").update_received_state()
        cancelled_moves.mapped("rma_id").update_replaced_state()
        return res

    def _action_done(self, cancel_backorder=False):
        """Avoids to validate stock.move with less quantity than the
        quantity in the linked receiver RMA. It also set the appropriated
        linked RMA to 'received' or 'delivered'.
        """
        for move in self.filtered(lambda r: r.state not in ("done", "cancel")):
            rma_receiver = move.sudo().rma_receiver_ids
            if rma_receiver and move.quantity_done != rma_receiver.product_uom_qty:
                raise ValidationError(
                    _(
                        "The quantity done for the product '%s' must "
                        "be equal to its initial demand because the "
                        "stock move is linked to an RMA (%s)."
                    )
                    % (move.product_id.name, move.rma_receiver_ids.name)
                )
        res = super()._action_done(cancel_backorder=cancel_backorder)
        move_done = self.filtered(lambda r: r.state == "done").sudo()
        # Set RMAs as received. We sudo so we can grant the operation even
        # if the stock user has no RMA permissions.
        to_be_received = (
            move_done.sudo()
            .mapped("rma_receiver_ids")
            .filtered(lambda r: r.state == "confirmed")
        )
        to_be_received.update_received_state_on_reception()
        # Set RMAs as delivered
        move_done.mapped("rma_id").update_replaced_state()
        move_done.mapped("rma_id").update_returned_state()
        return res

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        """The main use is that launched delivery RMAs doesn't merge
        two moves if they are linked to a different RMAs.
        """
        return super()._prepare_merge_moves_distinct_fields() + ["rma_id"]

    def _prepare_move_split_vals(self, qty):
        """Intended to the backport of picking linked to RMAs propagates the
        RMA link id.
        """
        res = super()._prepare_move_split_vals(qty)
        res["rma_id"] = self.sudo().rma_id.id
        return res

    def _prepare_return_rma_vals(self, original_picking):
        """hook method for preparing an RMA from the 'return picking wizard'."""
        self.ensure_one()
        partner = original_picking.partner_id
        if hasattr(original_picking, "sale_id") and original_picking.sale_id:
            partner_invoice_id = original_picking.sale_id.partner_invoice_id.id
            partner_shipping_id = original_picking.sale_id.partner_shipping_id.id
        else:
            partner_invoice_id = partner.address_get(["invoice"]).get("invoice", False)
            partner_shipping_id = partner.address_get(["delivery"]).get(
                "delivery", False
            )
        return {
            "user_id": self.env.user.id,
            "partner_id": partner.id,
            "partner_shipping_id": partner_shipping_id,
            "partner_invoice_id": partner_invoice_id,
            "origin": original_picking.name,
            "picking_id": original_picking.id,
            "move_id": self.origin_returned_move_id.id,
            "product_id": self.origin_returned_move_id.product_id.id,
            "product_uom_qty": self.product_uom_qty,
            "product_uom": self.product_uom.id,
            "reception_move_id": self.id,
            "company_id": self.company_id.id,
            "location_id": self.location_dest_id.id,
            "state": "confirmed",
        }


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        return super()._get_custom_move_fields() + ["rma_id"]
