# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_rma_vals(self):
        vals = super()._prepare_rma_vals()
        lot = self.lot_id
        vals["lot_id"] = lot.id
        if not self.move_id.restrict_lot_id:
            smls = self.move_id.move_line_ids.filtered(lambda x: x.lot_id == lot)
            vals["product_uom_qty"] = sum(smls.mapped("quantity"))
        return vals
