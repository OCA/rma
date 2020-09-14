# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Rma(models.Model):
    _inherit = "rma"

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        domain="["
               "    ('partner_id', 'child_of', commercial_partner_id),"
               "    ('state', 'in', ['sale', 'done']),"
               "]",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    allowed_picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        compute="_compute_allowed_picking_ids",
    )
    picking_id = fields.Many2one(
        domain="[('id', 'in', allowed_picking_ids)]",
    )
    allowed_move_ids = fields.Many2many(
        comodel_name='sale.order.line',
        compute="_compute_allowed_move_ids",
    )
    move_id = fields.Many2one(
        domain="[('id', 'in', allowed_move_ids)]",
    )
    allowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute="_compute_allowed_product_ids",
    )
    product_id = fields.Many2one(
        domain="[('id', 'in', allowed_product_ids)]",
    )

    @api.depends('partner_id', 'order_id')
    def _compute_allowed_picking_ids(self):
        domain = [('state', '=', 'done'),
                  ('picking_type_id.code', '=', 'outgoing')]
        for rec in self:
            # if rec.partner_id:
            commercial_partner = rec.partner_id.commercial_partner_id
            domain.append(('partner_id', 'child_of', commercial_partner.id))
            if rec.order_id:
                domain.append(('sale_id', '=', rec.order_id.id))
            rec.allowed_picking_ids = self.env['stock.picking'].search(domain)

    @api.depends('order_id', 'picking_id')
    def _compute_allowed_move_ids(self):
        for rec in self:
            if rec.order_id:
                order_move = rec.order_id.order_line.mapped('move_ids')
                rec.allowed_move_ids = order_move.filtered(
                    lambda r: r.picking_id == self.picking_id).ids
            else:
                rec.allowed_move_ids = self.picking_id.move_lines.ids

    @api.depends('order_id')
    def _compute_allowed_product_ids(self):
        for rec in self:
            if rec.order_id:
                order_product = rec.order_id.order_line.mapped('product_id')
                rec.allowed_product_ids = order_product.filtered(
                    lambda r: r.type in ['consu', 'product']).ids
            else:
                rec.allowed_product_ids = self.env['product.product'].search(
                    [('type', 'in', ['consu', 'product'])]).ids

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self.order_id = False
        return res

    @api.onchange('order_id')
    def _onchange_order_id(self):
        self.product_id = self.picking_id = False

    def _prepare_refund(self, invoice_form, origin):
        """Inject salesman from sales order (if any)"""
        res = super()._prepare_refund(invoice_form, origin)
        if self.order_id:
            invoice_form.user_id = self.order_id.user_id
        return res
