# Copyright 2024 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RMA(models.Model):
    _inherit = "rma"

    repair_id = fields.Many2one("repair.order")

    @api.depends("remaining_qty", "state", "repair_id.state")
    def _compute_can_be_returned(self):
        for r in self:
            r.can_be_returned = (
                r.state in ["received", "waiting_return"]
                and r.remaining_qty > 0
                and r.repair_id.state != "cancel"
            )

    @api.depends("state", "repair_id.state")
    def _compute_can_be_replaced(self):
        for r in self:
            r.can_be_replaced = (
                r.state
                in [
                    "received",
                    "waiting_replacement",
                    "replaced",
                ]
                and r.repair_id.state == "cancel"
            )

    @api.depends("state", "repair_id.state")
    def _compute_can_be_refunded(self):
        for r in self:
            r.can_be_refunded = r.state == "received" and r.repair_id.state == "cancel"

    def action_create_repair_order(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "repair.action_repair_order_form"
        )
        action["view_mode"] = "form"
        action["views"] = [(False, "form")]
        action["target"] = "current"
        action["name"] = _("Create Repair Order")

        action["context"] = {
            "default_rma_ids": [self.id],
            "default_product_id": self.product_id.id,
            "default_location_id": self.location_id.id,
            "default_partner_id": self.partner_id.id,
        }
        if self.lot_id:
            action["context"]["default_lot_id"] = self.lot_id.id
        return action

    def action_view_rma_repair_order(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.order",
            "res_id": self.repair_id.id,
        }
