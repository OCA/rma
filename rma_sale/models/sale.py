# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # RMAs that were created from a sale order
    rma_ids = fields.One2many(
        comodel_name="rma",
        inverse_name="order_id",
        string="RMAs",
        copy=False,
    )
    rma_count = fields.Integer(string="RMA count", compute="_compute_rma_count")

    def _compute_rma_count(self):
        rma_data = self.env["rma"].read_group(
            [("order_id", "in", self.ids)], ["order_id"], ["order_id"]
        )
        mapped_data = {r["order_id"][0]: r["order_id_count"] for r in rma_data}
        for record in self:
            record.rma_count = mapped_data.get(record.id, 0)

    def _prepare_rma_wizard_line_vals(self, data):
        """So we can extend the wizard easily"""
        return {
            "product_id": data["product"].id,
            "quantity": data["quantity"],
            "allowed_quantity": data["quantity"],
            "sale_line_id": data["sale_line_id"].id,
            "uom_id": data["uom"].id,
            "picking_id": data["picking"] and data["picking"].id,
        }

    def action_create_rma(self):
        self.ensure_one()
        if self.state not in ["sale", "done"]:
            raise ValidationError(
                _("You may only create RMAs from a " "confirmed or done sale order.")
            )
        wizard_obj = self.env["sale.order.rma.wizard"]
        line_vals = [
            (0, 0, self._prepare_rma_wizard_line_vals(data))
            for data in self.get_delivery_rma_data()
        ]
        wizard = wizard_obj.with_context(active_id=self.id).create(
            {"line_ids": line_vals, "location_id": self.warehouse_id.rma_loc_id.id}
        )
        return {
            "name": _("Create RMA"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.order.rma.wizard",
            "res_id": wizard.id,
            "target": "new",
        }

    def action_view_rma(self):
        self.ensure_one()
        action = self.sudo().env.ref("rma.rma_action").read()[0]
        rma = self.rma_ids
        if len(rma) == 1:
            action.update(
                res_id=rma.id,
                view_mode="form",
                views=[],
            )
        else:
            action["domain"] = [("id", "in", rma.ids)]
        # reset context to show all related rma without default filters
        action["context"] = {}
        return action

    def get_delivery_rma_data(self):
        self.ensure_one()
        data = []
        for line in self.order_line:
            data += line.prepare_sale_rma_data()
        return data

    @api.depends("rma_ids.refund_id")
    def _get_invoiced(self):
        """Search for possible RMA refunds and link them to the order. We
        don't want to link their sale lines as that would unbalance the
        qtys to invoice wich isn't correct for this case"""
        res = super()._get_invoiced()
        for order in self:
            refunds = order.sudo().rma_ids.mapped("refund_id")
            if not refunds:
                continue
            order.invoice_ids += refunds
            order.invoice_count = len(order.invoice_ids)
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_delivery_move(self):
        self.ensure_one()
        return self.move_ids.filtered(
            lambda r: (
                self == r.sale_line_id
                and r.state == "done"
                and not r.scrapped
                and r.location_dest_id.usage == "customer"
                and (
                    not r.origin_returned_move_id
                    or (r.origin_returned_move_id and r.to_refund)
                )
            )
        )

    def prepare_sale_rma_data(self):
        self.ensure_one()
        # Method helper to filter chained moves

        def _get_chained_moves(_moves, done_moves=None):
            moves = _moves.browse()
            done_moves = done_moves or _moves.browse()
            for move in _moves:
                if move.location_dest_id.usage == "customer":
                    moves |= move.returned_move_ids
                else:
                    moves |= move.move_dest_ids
            done_moves |= _moves
            moves = moves.filtered(
                lambda r: r.state in ["partially_available", "assigned", "done"]
            )
            if not moves:
                return moves
            moves -= done_moves
            moves |= _get_chained_moves(moves, done_moves)
            return moves

        product = self.product_id
        if self.product_id.type not in ["product", "consu"]:
            return {}
        moves = self.get_delivery_move()
        data = []
        if moves:
            for move in moves:
                # Look for chained moves to check how many items we can allow
                # to return. When a product is re-delivered it should be
                # allowed to open an RMA again on it.
                qty = move.product_uom_qty
                for _move in _get_chained_moves(move):
                    factor = 1
                    if _move.location_dest_id.usage != "customer":
                        factor = -1
                    qty += factor * _move.product_uom_qty
                # If by chance we get a negative qty we should ignore it
                qty = max(0, qty)
                data.append(
                    {
                        "product": move.product_id,
                        "quantity": qty,
                        "uom": move.product_uom,
                        "picking": move.picking_id,
                        "sale_line_id": self,
                    }
                )
        else:
            data.append(
                {
                    "product": product,
                    "quantity": self.qty_delivered,
                    "uom": self.product_uom,
                    "picking": False,
                    "sale_line_id": self,
                }
            )
        return data
