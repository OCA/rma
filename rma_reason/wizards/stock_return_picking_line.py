# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockReturnPickingLine(models.TransientModel):

    _inherit = "stock.return.picking.line"

    rma_reason_id = fields.Many2one(
        comodel_name="rma.reason",
        compute="_compute_rma_reason_id",
        store=True,
        readonly=False,
        string="RMA Reason",
    )
    is_rma_reason_required = fields.Boolean(
        related="wizard_id.company_id.is_rma_reason_required"
    )
    rma_operation_domain = fields.Binary(compute="_compute_rma_operation_domain")

    @api.depends("wizard_id.rma_reason_id")
    def _compute_rma_reason_id(self):
        for rec in self:
            if rec.wizard_id.rma_reason_id:
                rec.rma_reason_id = rec.wizard_id.rma_reason_id

    def _prepare_rma_vals(self):
        self.ensure_one()
        vals = super()._prepare_rma_vals()
        vals["reason_id"] = self.rma_reason_id.id
        return vals

    @api.depends("rma_reason_id")
    def _compute_rma_operation_domain(self):
        for rec in self:
            if rec.rma_reason_id and rec.rma_reason_id.allowed_operation_ids:
                rec.rma_operation_domain = [
                    ("id", "in", rec.rma_reason_id.allowed_operation_ids.ids)
                ]
            else:
                rec.rma_operation_domain = []
