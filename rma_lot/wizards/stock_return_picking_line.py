# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockReturnPickingLine(models.TransientModel):

    _inherit = "stock.return.picking.line"

    def _prepare_rma_vals(self):
        self.ensure_one()
        vals = super()._prepare_rma_vals()
        if not self.rma_operation_id.different_return_product:
            vals.update({"lot_id": self.lot_id.id})
        return vals
