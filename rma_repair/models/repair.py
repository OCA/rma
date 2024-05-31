# Copyright 2024 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    rma_ids = fields.One2many(
        comodel_name="rma",
        inverse_name="repair_id",
        string="RMAs",
    )

    def action_view_repair_rma(self):
        return {
            "name": "RMAs - " + self.name,
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "rma",
            "domain": [("id", "in", self.rma_ids.ids)],
        }
