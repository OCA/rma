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
            rec.rma_count = len(rec.move_lines.mapped("rma_ids"))

    def copy(self, default=None):
        self.ensure_one()
        if self.env.context.get("set_rma_picking_type"):
            location_dest_id = default["location_dest_id"]
            warehouse = self.env["stock.warehouse"].search(
                [("rma_loc_id", "parent_of", location_dest_id)], limit=1
            )
            if warehouse:
                default["picking_type_id"] = warehouse.rma_in_type_id.id
        return super().copy(default)

    def action_view_rma(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rma.rma_action")
        rma = self.move_lines.mapped("rma_ids")
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
                view_id=False,
                views=False,
            )
        else:
            action["domain"] = [("id", "in", rma.ids)]
        return action
