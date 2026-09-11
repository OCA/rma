# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_count = fields.Integer(
        string="RMA count",
        compute="_compute_rma_count",
    )

    def _compute_rma_count(self):
        for rec in self:
            rec.rma_count = len(rec.move_ids.mapped("rma_ids"))

    def action_view_rma(self):
        self.ensure_one()
        return self.move_ids.rma_ids._get_records_action()
