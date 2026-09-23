# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _is_restocking_fee_chargeable(self):
        """
        In RMA process only the last move of the return chain is chargeable.
        """
        res = super()._is_restocking_fee_chargeable()
        if self.first_move_id.rma_receiver_ids:
            if self.move_dest_ids:
                return False
            if self.charge_restocking_fee:
                # Need to return True here because in super(), result is False
                # if the move has no origin_returned_move_id
                return True

        return res

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        move_chargeable = self.filtered(
            lambda r: r.state == "done" and r._is_restocking_fee_chargeable()
        ).sudo()
        move_chargeable.sudo().mapped(
            "first_move_id.rma_receiver_ids"
        )._create_restocking_fee_invoice()
        return res
