# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        move_done = self.filtered(lambda r: r.state == "done").sudo()
        move_done.sudo().mapped("rma_receiver_ids")._create_restocking_fee_invoice()
        return res
