# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_restocking_fee_line_value(self, stock_move):
        vals = super()._get_restocking_fee_line_value(stock_move)
        rma = stock_move.mapped("first_move_id.rma_receiver_ids")
        if not rma:
            return vals
        vals["price_unit"] = rma._get_restocking_fee_amount()
        return vals
