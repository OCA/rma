# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.stock.models.stock_rule import ProcurementGroup


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _prepare_rma_vals(self, group_id: ProcurementGroup) -> dict:
        self.ensure_one()
        return {
            "move_id": self.move_id.id,
            "product_id": self.product_id.id,
            "product_uom_qty": self.qty_done,
            "product_uom": self.product_uom_id.id,
            "location_id": self.location_dest_id.id,
            "partner_id": self.move_id.partner_id.id,
            "lot_id": self.lot_id.id,
            "batch_id": self.picking_id.rma_batch_id.id,
            "operation_id": self.picking_id.rma_batch_id.operation_id.id
            if self.picking_id.rma_batch_id
            else self.picking_type_id.rma_create_operation_id.id,
            "reception_move_id": self.move_id.id,
            "procurement_group_id": group_id.id,
        }
