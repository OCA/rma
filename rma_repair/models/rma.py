# Copyright 2024 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RMA(models.Model):
    _inherit = "rma"

    repair_id = fields.Many2one("repair.order")

    @api.depends("repair_id.state")
    def _compute_can_be_returned(self):
        res = super()._compute_can_be_returned()
        for r in self:
            r.can_be_returned = r.can_be_returned and (
                not r.repair_id or r.repair_id.state == "done"
            )
        return res

    @api.depends("repair_id.state")
    def _compute_can_be_replaced(self):
        res = super()._compute_can_be_replaced()
        for r in self:
            r.can_be_replaced = r.can_be_replaced and (
                not r.repair_id or r.repair_id.state == "cancel"
            )
        return res

    @api.depends("repair_id.state")
    def _compute_can_be_refunded(self):
        res = super()._compute_can_be_refunded()
        for r in self:
            r.can_be_refunded = r.can_be_refunded and (
                not r.repair_id or r.repair_id.state == "cancel"
            )
        return res

    def action_create_repair_order(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "repair.action_repair_order_form"
        )
        action.update(
            {
                "view_mode": "form",
                "views": [(False, "form")],
                "name": _("Create Repair Order"),
                "context": {
                    "default_rma_ids": [self.id],
                    "default_product_id": self.product_id.id,
                    "default_location_id": self.location_id.id,
                    "default_partner_id": self.partner_id.id,
                },
            }
        )
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
