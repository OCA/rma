# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Rma(models.Model):
    _inherit = "rma"

    batch_id = fields.Many2one(
        "rma.batch", string="RMA Batch", index=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        compute="_compute_partner_id", store=True, readonly=False
    )
    user_id = fields.Many2one(compute="_compute_user_id", store=True, readonly=False)
    tag_ids = fields.Many2many(compute="_compute_tag_ids", store=True, readonly=False)
    operation_id = fields.Many2one(
        compute="_compute_operation_id", store=True, readonly=False
    )

    @api.depends("batch_id.operation_id")
    def _compute_operation_id(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.batch_id.operation_id:
                rec.operation_id = rec.batch_id.operation_id

    @api.depends("batch_id.partner_id")
    def _compute_partner_id(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.batch_id.partner_id:
                rec.partner_id = rec.batch_id.partner_id

    @api.depends("batch_id.user_id")
    def _compute_user_id(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.batch_id.user_id:
                rec.user_id = rec.batch_id.user_id

    @api.depends("batch_id.tag_ids")
    def _compute_tag_ids(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.batch_id.tag_ids:
                rec.tag_ids = rec.batch_id.tag_ids

    @api.depends("user_id", "batch_id.team_id")
    def _compute_team_id(self):
        res = super()._compute_team_id()
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.batch_id.team_id:
                rec.team_id = rec.batch_id.team_id
        return res

    @api.depends("picking_id", "product_id", "company_id", "batch_id.location_id")
    def _compute_location_id(self):
        """Override to consider RMA Batch location"""
        super()._compute_location_id()
        # Apply RMA Batch location if set
        for record in self:
            if record.state != "draft":
                continue
            if record.batch_id.location_id:
                record.location_id = record.batch_id.location_id

        return

    @api.constrains("batch_id", "partner_id")
    def _check_batch_partner(self):
        for rec in self:
            if (
                rec.batch_id
                and rec.partner_id
                and rec.batch_id.partner_id != rec.partner_id
            ):
                raise ValidationError(
                    _("All RMAs in a batch must belong to the same partner")
                )

    def action_show_rma(self):
        self.ensure_one()
        return {
            "name": self.display_name,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(False, "form")],
            "res_id": self.id,
        }
