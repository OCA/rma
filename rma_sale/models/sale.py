# Copyright 2020 Tecnativa - Ernesto Tejeda
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

        def destination_moves(_move):
            return _move.mapped("move_dest_ids").filtered(
                lambda r: r.state in ["partially_available", "assigned", "done"]
            )

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
                qty_returned = 0
                move_dest = destination_moves(move)
                # With the return of the return of the return we could have an
                # infinite loop, so we should avoid it dropping already explored
                # move_dest_ids
                visited_moves = move + move_dest
                while move_dest:
                    qty_returned -= sum(move_dest.mapped("product_uom_qty"))
                    move_dest = destination_moves(move_dest) - visited_moves
                    if move_dest:
                        visited_moves += move_dest
                        qty += sum(move_dest.mapped("product_uom_qty"))
                        move_dest = destination_moves(move_dest) - visited_moves
                # If by chance we get a negative qty we should ignore it
                qty = max(0, sum((qty, qty_returned)))
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
