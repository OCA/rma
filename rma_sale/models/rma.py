# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .rma_operation import TIMING_REFUND_SO


class Rma(models.Model):
    _inherit = "rma"

    order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        domain="["
        "    ('partner_id', 'child_of', commercial_partner_id),"
        "    ('state', 'in', ['sale', 'done']),"
        "]",
        readonly=True,
        states={"draft": [("readonly", False)]},
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
        comodel_name="sale.order.line",
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
                rec.allowed_move_ids = self.picking_id.move_lines.ids

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

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self.order_id = False
        return res

    @api.onchange("order_id")
    def _onchange_order_id(self):
        self.product_id = self.picking_id = False

    def _prepare_refund(self, invoice_form, origin):
        """Inject salesman from sales order (if any)"""
        res = super()._prepare_refund(invoice_form, origin)
        if self.order_id:
            invoice_form.invoice_user_id = self.order_id.user_id
        return res

    def _get_refund_line_price_unit(self):
        """Get the sale order price unit"""
        if self.sale_line_id:
            return self.sale_line_id.price_unit
        return super()._get_refund_line_price_unit()

    def _get_refund_line_product(self):
        """To be overriden in a third module with the proper origin values
        in case a kit is linked with the rma"""
        if not self.sale_line_id:
            return super()._get_refund_line_product()
        return self.sale_line_id.product_id

    def _prepare_refund_line(self, line_form):
        """Add line data"""
        super()._prepare_refund_line(line_form)
        line = self.sale_line_id
        if line:
            line_form.discount = line.discount
            line_form.sequence = line.sequence

    def _prepare_procurement_group_values(self):
        values = super()._prepare_procurement_group_values()
        if not self.env.context.get("ignore_rma_sale_order") and self.order_id:
            values["sale_id"] = self.order_id.id
        return values

    def _create_delivery_procurement_group(self):
        # Set the context to avoid creating a new sale.order.line
        # see odoo's core code addons/sale_stock/models/stock.py stock.picking _action_done
        self = self.with_context(ignore_rma_sale_order=True)
        return super()._create_delivery_procurement_group()

    def _update_procurement_values_for_sale_line_refund(self, values):
        # If a rma should refunded via the sale.orders
        # the sale_line_id must be set on a stock.move
        # this in- or decreases the qty_delivered of a sale.order.line
        if (
            self.operation_id.create_refund_timing == TIMING_REFUND_SO
            and self.sale_line_id
        ):
            values["sale_line_id"] = self.sale_line_id.id

    def _prepare_reception_procurement_values(self, group=None):
        values = super()._prepare_reception_procurement_values(group)
        self._update_procurement_values_for_sale_line_refund(values)
        if values.get("sale_line_id"):
            values["to_refund"] = True
        return values

    def _prepare_delivery_procurement_values(self, scheduled_date=None):
        values = super()._prepare_delivery_procurement_values(scheduled_date)
        self._update_procurement_values_for_sale_line_refund(values)
        if values.get("sale_line_id"):
            values.pop("move_orig_ids")
        return values
