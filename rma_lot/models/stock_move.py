# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _set_restrict_lot_id_from_rma(self, lot):
        """This method can be extended and/or used by other modules to intercept
        the change from the rma.
        """
        self.restrict_lot_id = lot
        if self.picked:
            # It is important that if stock.move is set as picked=True, it be changed
            # so that the _do_unreserve() method removes stock.move.line and creates
            # a new one with the correct lot.
            self.move_line_ids.picked = False
        self._do_unreserve()
        self.filtered(
            lambda move: move.state in ("confirmed", "partially_available")
        )._action_assign()
