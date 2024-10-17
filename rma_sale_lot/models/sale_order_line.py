# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import models
from odoo.tools.float_utils import float_round


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    def _get_qty_done_by_product_lot(self, moves):
        res = defaultdict(float)
        for group in self.env["stock.move.line"].read_group(
            [
                ("move_id", "in", moves.ids),
                ("state", "=", "done"),
                ("move_id.scrapped", "=", False),
            ],
            ["qty_done:sum"],
            ["product_id", "lot_id"],
            lazy=False,
        ):
            lot_id = group.get("lot_id")[0] if group.get("lot_id") else False
            product_id = group.get("product_id")[0]
            qty_done = group.get("qty_done")
            res[(product_id, lot_id)] += qty_done
        return res

    def prepare_sale_rma_data(self):
        self.ensure_one()
        if self.product_id.type not in ["product", "consu"]:
            return {}
        if not self.product_id.tracking or self.product_id.tracking == "none":
            return super().prepare_sale_rma_data()
        moves = self.get_delivery_move()
        data = []
        qty_done_by_product_lot = self._get_qty_done_by_product_lot(moves)
        for (product_id, lot_id), qty_done in qty_done_by_product_lot.items():
            data.append(
                self._prepare_sale_rma_data_line(moves, product_id, lot_id, qty_done)
            )
        return data

    def _prepare_sale_rma_data_line(self, moves, product_id, lot_id, qty_done):
        moves = moves.move_line_ids.filtered(
            lambda ml, p_id=product_id, l_id=lot_id: ml.product_id.id == p_id
            and ml.lot_id.id == l_id
        ).move_id
        quantity = qty_done
        for returned_move in moves.returned_move_ids.filtered(
            lambda r: r.state in ["partially_available", "assigned", "done"]
        ):
            if (
                returned_move.restrict_lot_id
                and returned_move.restrict_lot_id.id == lot_id
                or not lot_id
            ):
                if returned_move.state in ("partially_available", "assigned"):
                    quantity -= sum(returned_move.move_line_ids.mapped("reserved_qty"))
                elif returned_move.state == "done":
                    quantity -= returned_move.product_qty
        quantity = float_round(
            quantity, precision_rounding=moves.product_id.uom_id.rounding
        )
        return {
            "product": moves.product_id,
            "quantity": quantity,
            "uom": moves.product_uom,
            "picking": moves.picking_id[0],
            "sale_line_id": self,
            "lot_id": lot_id,
        }
