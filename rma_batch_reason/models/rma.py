# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Rma(models.Model):
    _inherit = "rma"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("batch_id") and not vals.get("reason_id"):
                batch = self.env["rma.batch"].browse(vals["batch_id"])
                if batch.reason_id:
                    vals["reason_id"] = batch.reason_id.id
        return super().create(vals_list)
