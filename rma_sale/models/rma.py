# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression

ORDER_STATE_DOMAIN = [("state", "in", ["sale", "done"])]


class Rma(models.Model):
    _inherit = "rma"

    def _domain_product_id(self):
        return [("type", "in", ["consu", "product"])]

    order_id = fields.Many2one(
        "sale.order",
        "Sale Order",
        domain=ORDER_STATE_DOMAIN,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    allowed_picking_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_allowed_picking_ids",
    )
    picking_id = fields.Many2one(domain="[('id', 'in', allowed_picking_ids)]")
    allowed_move_ids = fields.Many2many(
        "sale.order.line",
        compute="_compute_allowed_move_ids",
    )
    move_id = fields.Many2one(domain="[('id', 'in', allowed_move_ids)]")
    sale_line_id = fields.Many2one(
        related="move_id.sale_line_id",
    )
    product_id = fields.Many2one(domain=lambda self: self._domain_product_id())

    @api.depends("partner_id", "order_id")
    def _compute_allowed_picking_ids(self):
        domain = [("state", "=", "done"), ("picking_type_id.code", "=", "outgoing")]
        for rec in self:
            if rec.partner_id:
                commercial_partner = rec.partner_id.commercial_partner_id
                domain.append(("partner_id", "child_of", commercial_partner.id))
            if rec.order_id:
                domain.append(("sale_id", "=", rec.order_id.id))
            rec.allowed_picking_ids = self.env["stock.picking"].search(domain)

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

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()

        def add_order_domain(r, domain):
            r = r or {}
            _domain = r.setdefault("domain", {})
            _domain["order_id"] = domain
            return r

        PARTNER_DOMAIN = [
            ("partner_id", "child_of", self.partner_id.commercial_partner_id.id)
        ]
        if not self.partner_id or not self.order_id.filtered_domain(PARTNER_DOMAIN):
            self.order_id = False
            if not self.partner_id:
                res = add_order_domain(res, ORDER_STATE_DOMAIN)
            else:
                res = add_order_domain(
                    res,
                    expression.AND(
                        [
                            ORDER_STATE_DOMAIN,
                            PARTNER_DOMAIN,
                        ]
                    ),
                )
        return res

    @api.onchange("order_id")
    def _onchange_order_id(self):
        self.product_id = self.picking_id = False
        domain = self._domain_product_id()
        if self.order_id:
            domain += [("id", "in", self.order_id.order_line.mapped("product_id").ids)]
            self.partner_id = self.order_id.partner_id
            self.partner_invoice_id = self.order_id.partner_invoice_id
            self.partner_shipping_id = self.order_id.partner_shipping_id
        return {"domain": {"product_id": domain}}

    @api.onchange("order_id", "product_id")
    def _onchange_order_id_product_id(self):
        if not self.order_id or not self.product_id:
            self.picking_id = self.move_id = False
            return

        allowed_moves = self.allowed_picking_ids.filtered(
            lambda p: self.product_id in p.move_lines.product_id
        ).move_lines

        if not allowed_moves:
            self.picking_id = self.move_id = False
            return

        last_move = allowed_moves.sorted(
            key=lambda m: m.picking_id.date_done, reverse=True
        )[0]
        self.move_id = last_move
        self.picking_id = last_move.picking_id

    @api.onchange("picking_id")
    def _onchange_picking_id(self):
        if not self.picking_id:
            self.move_id = False

        if self.move_id not in self.picking_id.move_lines and self.product_id:
            self.move_id = self.picking_id.move_lines.filtered(
                lambda m: m.product_id == self.product_id
            )

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
