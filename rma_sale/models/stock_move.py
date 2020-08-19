# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_return_rma_vals(self, original_picking):
        res = super()._prepare_return_rma_vals(original_picking)
        res.update(order_id=original_picking.sale_id.id)
        return res
