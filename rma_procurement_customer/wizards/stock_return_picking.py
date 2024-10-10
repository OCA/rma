# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockReturnPicking(models.TransientModel):

    _inherit = "stock.return.picking"

    def _prepare_rma_vals(self):
        vals = super()._prepare_rma_vals()
        if vals.get("procurement_group_id") and self.picking_id.customer_id:
            procurement_group = self.env["procurement.group"].browse(
                vals.get("procurement_group_id")
            )
            procurement_group.customer_id = self.picking_id.customer_id
        return vals
