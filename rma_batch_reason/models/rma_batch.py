# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaBatch(models.Model):
    _inherit = "rma.batch"

    reason_id = fields.Many2one(
        "rma.reason",
        string="Reason",
        help="Reason for the return, applied to all RMAs in the batch.",
    )

    @api.onchange("reason_id")
    def _onchange_reason_id(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.reason_id:
                rec.rma_ids.filtered(
                    lambda r: not r.reason_id
                ).reason_id = rec.reason_id
