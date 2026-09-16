# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class Rma(models.Model):
    _inherit = "rma"
    has_sale_auto_detect_issue = fields.Boolean(readonly=True)
    ignore_sale_auto_detect = fields.Boolean(readonly=True)
    sale_auto_detect_note = fields.Text(readonly=True)
    return_eligibility_days = fields.Integer(
        string="Return eligibility duration (days)",
        help=(
            "Defines the time window in which sales can be linked "
            "automatically to RMA lines. "
            "Example: 30 days (change of mind), 730 days (warranty), "
            "0 to disable, or a large number for lifetime warranty."
        ),
        compute="_compute_return_eligibility_days",
        store=True,
        readonly=False,
    )
    return_eligibility_period_exceeded = fields.Boolean(
        compute="_compute_return_eligibility_period_exceeded"
    )

    @api.depends("order_id.date_order", "return_eligibility_days", "state")
    def _compute_return_eligibility_period_exceeded(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != "draft" or not rec.order_id or not rec.order_id.date_order:
                rec.return_eligibility_period_exceeded = False
                continue
            deadline = rec.order_id.date_order + timedelta(
                days=rec.return_eligibility_days
            )
            rec.return_eligibility_period_exceeded = today > deadline.date()

    @api.depends("operation_id")
    def _compute_return_eligibility_days(self):
        for rec in self:
            if not rec.operation_id:
                continue
            rec.return_eligibility_days = rec.operation_id.return_eligibility_days

    def action_link_rma_to_sale_line(self):
        """automatically link RMAs to the most relevant sale order lines"""
        sol_model = self.env["sale.order.line"]
        _filter_sol = self._filter_sale_lines_by_delivery_move
        _sort_sol = self._sort_sale_lines_by_order_date
        self.write(
            {"has_sale_auto_detect_issue": False, "sale_auto_detect_note": False}
        )
        rma_to_link = self.filtered(
            lambda r: not r.sale_line_id and not r.ignore_sale_auto_detect
        )
        unlinked_rmas = self.browse()
        for rma in rma_to_link:
            if rma.order_id:
                sale_lines = rma.order_id.order_line.filtered(
                    lambda line, r=rma: line.product_id == r.product_id
                )
            else:
                sale_lines = sol_model.search(
                    rma._get_eligible_sale_lines_domain(),
                )

            sale_lines = _filter_sol(sale_lines)
            sale_lines = _sort_sol(sale_lines)
            unlinked_rmas |= rma._link_rma_to_sale_line(sale_lines)
        # Mark remaining unmatched RMAs
        not_linked_rmas = (rma_to_link | unlinked_rmas).filtered(
            lambda r: not r.sale_line_id
        )
        not_linked_rmas.has_sale_auto_detect_issue = True
        not_linked_rmas.sale_auto_detect_note = _(
            "No delivery move found or insufficient delivered quantity."
        )
        return True

    def _get_eligible_sale_lines_domain(self):
        self.ensure_one()
        return_eligibility_days = self.return_eligibility_days or 0
        oldest_date = fields.Date.to_date(fields.Date.today()) - timedelta(
            days=return_eligibility_days
        )
        return [
            ("order_id.partner_id", "child_of", self.partner_id.id),
            ("state", "in", ["sale", "done"]),
            ("order_id.date_order", ">=", oldest_date),
            ("product_id", "=", self.product_id.id),
        ]

    @api.model
    def _filter_sale_lines_by_delivery_move(self, sale_lines):
        """return only sale order lines whose delivered moves still have returnable
        quantity"""
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        return sale_lines.filtered(
            lambda sol: any(
                m.state == "done"
                and float_compare(
                    m.rma_returnable_uom_qty, 0, precision_digits=precision
                )
                > 0
                for m in sol.move_ids
            )
        )

    @api.model
    def _sort_sale_lines_by_order_date(self, sale_lines):
        return sale_lines.sorted(lambda sol: (sol.order_id.date_order, sol.id))

    def _link_rma_to_sale_line(self, sale_lines):
        """match between rmas and sale lines"""
        matched_rmas = self.browse()
        if not sale_lines:
            return matched_rmas
        sale_line_delivered_qty = self._get_sale_line_returnable_qty(sale_lines)
        rmas = self.sorted("date")
        sale_lines = sale_lines.sorted(lambda sol: (sol.order_id.date_order, sol.id))

        rma_index = 0
        sale_index = 0

        while rma_index < len(rmas) and sale_index < len(sale_lines):
            rma = rmas[rma_index]
            sale_line = sale_lines[sale_index]
            remaining_qty = sale_line_delivered_qty.get(sale_line.id, 0.0)

            if remaining_qty <= 0:
                sale_index += 1
                continue

            rma_qty = rma.product_uom_qty

            if rma_qty == remaining_qty:
                # perfect match
                rma._link_rma_to_delivery_move(sale_line)
                sale_line_delivered_qty[sale_line.id] = 0.0
                rma_index += 1
                sale_index += 1
            elif rma_qty > remaining_qty:
                # rma needs more than available on this sale line
                # we copy RMA for the matched qty
                matched_rma = rma.copy({"product_uom_qty": remaining_qty})
                # reduce qty on original RMA
                rma.product_uom_qty = rma_qty - remaining_qty
                # link the matched copy to the sale line
                matched_rma._link_rma_to_delivery_move(sale_line)
                sale_line_delivered_qty[sale_line.id] = 0.0
                sale_index += 1
                matched_rmas |= matched_rma
            else:
                # rma quantity smaller than available delivered qty
                rma._link_rma_to_delivery_move(sale_line, qty_limit=rma_qty)
                sale_line_delivered_qty[sale_line.id] = remaining_qty - rma_qty
                rma_index += 1
        return matched_rmas

    @api.model
    def _get_sale_line_returnable_qty(self, sale_lines):
        """return a dict mapping sale_line.id -> delivered quantity"""
        return {
            line.id: sum(line.move_ids.mapped("rma_returnable_uom_qty"))
            if line.move_ids
            else 0.0
            for line in sale_lines
        }

    def _link_rma_to_delivery_move(self, sale_line, qty_limit=None):
        """assign stock moves from a sale line to an rma
        qty_limit can be used to cap the total assigned quantity
        """
        self.ensure_one()
        delivery_moves = sale_line.move_ids.filtered(
            lambda m: m.state == "done"
        ).sorted(lambda m: (m.date, m.id))
        if not delivery_moves:
            return

        total_assigned = 0.0
        for i, move in enumerate(delivery_moves):
            move_qty = move.rma_returnable_uom_qty
            if qty_limit and total_assigned + move_qty > qty_limit:
                move_qty = qty_limit - total_assigned
            total_assigned += move_qty
            if not move_qty or qty_limit and total_assigned > qty_limit:
                break
            values = {
                "move_id": move.id,
                "picking_id": move.picking_id.id,
                "product_uom_qty": move_qty,
                "order_id": sale_line.order_id.id,
            }
            if i == 0:
                self.write(values)
            else:
                # duplicate for each additional move
                self.copy(values)

    def action_draft(self):
        res = super().action_draft()
        self.filtered(lambda r: r.state == "draft").write(
            {"has_sale_auto_detect_issue": False, "sale_auto_detect_note": False}
        )
        return res

    def action_confirm(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        for rec in self:
            if rec.move_id and (
                float_compare(
                    rec.move_id.rma_returnable_uom_qty,
                    0,
                    precision_digits=precision,
                )
                < 0
            ):
                raise ValidationError(
                    _(
                        "The quantity to return exceeds the remaining returnable "
                        "quantity for this delivery."
                    )
                )

        return super().action_confirm()
