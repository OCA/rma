# Copyright 2024 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RMA(models.Model):
    _inherit = "rma"

    repair_id = fields.Many2one("repair.order")
    can_be_repaired = fields.Boolean(compute="_compute_can_be_repaired")

    @api.depends("repair_id", "state", "operation_id.action_create_repair")
    def _compute_can_be_repaired(self):
        """Compute 'can_be_repaired'. This field controls the visibility
        of the 'repair' button in the rma form
        view and determinate if the product can be repaired
        """
        for r in self:
            r.can_be_repaired = not r.repair_id and (
                (
                    r.operation_id.action_create_repair
                    in ("manual_after_receipt", "automatic_after_receipt")
                    and r.state in ["received", "waiting_return"]
                )
                or (
                    r.operation_id.action_create_repair
                    in ("manual_on_confirm", "automatic_on_confirm")
                    and r.state == "confirmed"
                )
            )

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

    def _get_repair_order_default_vals(self):
        self.ensure_one()
        return {
            "default_rma_ids": [self.id],
            "default_product_id": self.product_id.id,
            "default_product_location_src_id": self.location_id.id,
            "default_partner_id": self.partner_id.id,
            "default_product_qty": self.product_uom_qty,
            "default_product_uom": self.product_uom.id,
            "default_address_id": self.partner_shipping_id.id,
            "default_partner_invoice_id": self.partner_invoice_id.id,
            "default_picking_id": self.reception_move_id.picking_id.id,
        }

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
                "context": self._get_repair_order_default_vals(),
            }
        )
        return action

    def action_view_rma_repair_order(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.order",
            "res_id": self.repair_id.id,
        }

    def _create_repair(self):
        self.ensure_one()
        if self.repair_id:
            return self.repair_id
        return (
            self.env["repair.order"]
            .with_context(**self._get_repair_order_default_vals())
            .create({})
        )

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            if rec.operation_id.action_create_repair == "automatic_on_confirm":
                rec._create_repair()
        return res

    def update_received_state_on_reception(self):
        res = super().update_received_state_on_reception()
        for rec in self:
            if rec.operation_id.action_create_repair == "automatic_after_receipt":
                rec._create_repair()
        return res
