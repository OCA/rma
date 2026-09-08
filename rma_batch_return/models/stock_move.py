# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.stock.models.stock_rule import ProcurementGroup


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_rma_vals(
        self, group_id: ProcurementGroup | bool = False
    ) -> list[dict]:
        vals_list = []
        group_obj = self.env["procurement.group"]
        for move in self:
            if not group_id:
                group_id = group_obj.create({})
            vals_list.append(
                {
                    "move_id": move.id,
                    "product_id": move.product_id.id,
                    "product_uom_qty": move.quantity,
                    "product_uom": move.product_id.uom_id.id,
                    "location_id": move.location_dest_id.id,
                    "partner_id": move.partner_id.id,
                    "lot_id": move.lot_ids.id,
                    "batch_id": move.picking_id.rma_batch_id.id,
                    "operation_id": move.picking_id.rma_batch_id.operation_id.id
                    if move.picking_id.rma_batch_id
                    else move.picking_type_id.rma_create_operation_id.id,
                    "reception_move_id": move.id,
                    "procurement_group_id": group_id.id,
                }
            )
        return vals_list

    def _action_done(self, cancel_backorder=False):
        for picking, moves in self.partition("picking_id").items():
            if picking.picking_type_id.create_rma_at_confirm:
                group = self.env["procurement.group"].create({})
                rma_vals = moves._prepare_rma_vals(group_id=group)
                rmas = self.env["rma"].create(rma_vals)
                # Ensure required computed fields in constraint are correclty
                # computed before write
                batch = self.env["rma.batch"]._create_and_assign_rma(rmas)
                rmas.invalidate_recordset()
                rmas.write({"state": "confirmed"})
                picking.write({"rma_batch_id": batch.id})

        res = super()._action_done(cancel_backorder=cancel_backorder)

        return res
