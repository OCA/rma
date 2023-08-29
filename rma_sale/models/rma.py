# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class Rma(models.Model):
    _inherit = "rma"

    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        domain="["
        "    ('partner_id', 'child_of', commercial_partner_id),"
        "    ('state', 'in', ['sale', 'done']),"
        "]",
        store=True,
        readonly=False,
        compute="_compute_order_id",
    )
    allowed_picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        compute="_compute_allowed_picking_ids",
    )
    picking_id = fields.Many2one(
        domain="(order_id or partner_id) and [('id', 'in', allowed_picking_ids)] or "
        "[('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing')] "
    )
    allowed_move_ids = fields.Many2many(
        comodel_name="stock.move",
        compute="_compute_allowed_move_ids",
    )
    move_id = fields.Many2one(domain="[('id', 'in', allowed_move_ids)]")
    sale_line_id = fields.Many2one(
        related="move_id.sale_line_id",
    )
    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_allowed_product_ids",
    )
    product_id = fields.Many2one(
        domain="order_id and [('id', 'in', allowed_product_ids)] or "
        "[('type', 'in', ['consu', 'product'])]"
    )
    # Add index to this field, as we perform a search on it
    refund_id = fields.Many2one(index=True)

    @api.depends("partner_id", "order_id")
    def _compute_allowed_picking_ids(self):
        domain = [("state", "=", "done"), ("picking_type_id.code", "=", "outgoing")]
        for rec in self:
            domain2 = domain.copy()
            if rec.partner_id:
                commercial_partner = rec.partner_id.commercial_partner_id
                domain2.append(("partner_id", "child_of", commercial_partner.id))
            if rec.order_id:
                domain2.append(("sale_id", "=", rec.order_id.id))
            if domain2 != domain:
                rec.allowed_picking_ids = self.env["stock.picking"].search(domain2)
            else:
                rec.allowed_picking_ids = False  # don't populate a big list

    @api.depends("order_id", "picking_id")
    def _compute_allowed_move_ids(self):
        for rec in self:
            if rec.order_id:
                order_move = rec.order_id.order_line.mapped("move_ids")
                rec.allowed_move_ids = order_move.filtered(
                    lambda r: r.picking_id == self.picking_id and r.state == "done"
                ).ids
            else:
                rec.allowed_move_ids = self.picking_id.move_ids.ids

    @api.depends("order_id")
    def _compute_allowed_product_ids(self):
        for rec in self:
            if rec.order_id:
                order_product = rec.order_id.order_line.mapped("product_id")
                rec.allowed_product_ids = order_product.filtered(
                    lambda r: r.type in ["consu", "product"]
                ).ids
            else:
                rec.allowed_product_ids = False  # don't populate a big list

    @api.depends("partner_id")
    def _compute_order_id(self):
        """Empty sales order when changing partner."""
        self.order_id = False

    @api.onchange("order_id")
    def _onchange_order_id(self):
        self.product_id = self.picking_id = False

    def _link_refund_with_reception_move(self):
        """Perform the internal operations for linking the RMA reception move with the
        sales order line if applicable.
        """
        self.ensure_one()
        move = self.reception_move_id
        if (
            move
            and float_compare(
                self.product_uom_qty,
                move.product_uom_qty,
                precision_rounding=move.product_uom.rounding,
            )
            == 0
        ):
            self.reception_move_id.sale_line_id = self.sale_line_id.id
            self.reception_move_id.to_refund = True

    def _unlink_refund_with_reception_move(self):
        """Perform the internal operations for unlinking the RMA reception move with the
        sales order line.
        """
        self.ensure_one()
        self.reception_move_id.sale_line_id = False
        self.reception_move_id.to_refund = False

    def action_refund(self):
        """As we have made a refund, the return move + the refund should be linked to
        the source sales order line, to decrease both the delivered and invoiced
        quantity.

        NOTE: The refund line is linked to the SO line in `_prepare_refund_line`.
        """
        res = super().action_refund()
        for rma in self:
            if rma.sale_line_id:
                rma._link_refund_with_reception_move()
        return res

    def _prepare_refund_vals(self, origin=False):
        """Inject salesman from sales order (if any)"""
        vals = super()._prepare_refund_vals(origin=origin)
        if self.order_id:
            vals["invoice_user_id"] = self.order_id.user_id.id
        return vals

    def _prepare_refund_line_vals(self):
        """Add line data and link to the sales order, only if the RMA is for the whole
        move quantity. In other cases, incorrect delivered/invoiced quantities will be
        logged on the sales order, so better to let the operations not linked.
        """
        vals = super()._prepare_refund_line_vals()
        line = self.sale_line_id
        if line:
            vals["product_id"] = line.product_id.id
            vals["price_unit"] = line.price_unit
            vals["discount"] = line.discount
            vals["sequence"] = line.sequence
            move = self.reception_move_id
            if (
                move
                and float_compare(
                    self.product_uom_qty,
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                )
                == 0
            ):
                vals["sale_line_ids"] = [(4, line.id)]
        return vals
