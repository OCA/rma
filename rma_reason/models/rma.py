# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Rma(models.Model):

    _inherit = "rma"

    reason_id = fields.Many2one(comodel_name="rma.reason")
    is_rma_reason_required = fields.Boolean(related="company_id.is_rma_reason_required")
    operation_domain = fields.Binary(compute="_compute_operation_domain")

    @api.depends("reason_id")
    def _compute_operation_domain(self):
        for rec in self:
            if rec.reason_id and rec.reason_id.allowed_operation_ids:
                rec.operation_domain = [
                    ("id", "in", rec.reason_id.allowed_operation_ids.ids)
                ]
            else:
                rec.operation_domain = []
