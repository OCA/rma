# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_carrier_tracking_chained_pickings(self, skip_return_links=False):
        """Pickings reached through the chained moves, the same way
        `send_to_shipper` does to propagate the tracking number.

        :param skip_return_links: do not go across the links between a move and
            its return (customer return, RMA reception and RMA delivery), as they
            are different shipments.
        """
        self.ensure_one()
        pickings = self.browse()
        for field_name in ("move_orig_ids", "move_dest_ids"):
            explored_moves = moves = self.move_ids
            while moves:
                next_moves = self.env["stock.move"]
                for move in moves:
                    linked_moves = move[field_name]
                    if skip_return_links:
                        linked_moves = linked_moves.filtered(
                            lambda linked, move=move: not move._is_return_link(linked)
                        )
                    next_moves |= linked_moves
                moves = next_moves - explored_moves
                explored_moves |= moves
                pickings |= moves.picking_id
        return pickings - self

    def send_to_shipper(self):
        """Odoo propagates the tracking number to every chained picking, so the
        tracking number of an RMA delivery ends up in the returned delivery and in
        the RMA reception. Keep the tracking number of those pickings."""
        self.ensure_one()
        protected_pickings = (
            self._get_carrier_tracking_chained_pickings()
            - self._get_carrier_tracking_chained_pickings(skip_return_links=True)
        )
        tracking_refs = {
            picking: picking.carrier_tracking_ref for picking in protected_pickings
        }
        res = super().send_to_shipper()
        for picking, tracking_ref in tracking_refs.items():
            if picking.carrier_tracking_ref != tracking_ref:
                picking.carrier_tracking_ref = tracking_ref
        return res
