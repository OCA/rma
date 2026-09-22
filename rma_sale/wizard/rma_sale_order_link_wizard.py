# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RmaSaleOrderLinkWizard(models.TransientModel):

    _name = "rma.sale.order.link.wizard"
    _description = "Wizard to link existing rma to sale order"

    rma_id = fields.Many2one(comodel_name="rma")
    partner_id = fields.Many2one(related="rma_id.partner_id")
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('sale', 'done'))]",
    )
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line",
        required=True,
        compute="_compute_sale_line_id",
        store=True,
        readonly=False,
        domain="["
        "    ('order_id', '=', sale_order_id),"
        "    ('display_type', '=', False),"
        "    ('product_id.type', 'in', ('consu', 'product')),"
        "]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_id = res.get("rma_id") or self.env.context.get("default_rma_id")
        rma = self.env["rma"].browse(rma_id) if rma_id else self.env["rma"]
        sale_line = rma.sale_line_id
        sale_order = rma.order_id or sale_line.order_id
        if "sale_order_id" in fields_list and sale_order:
            res.setdefault("sale_order_id", sale_order.id)
        if "sale_line_id" in fields_list and sale_line:
            res.setdefault("sale_line_id", sale_line.id)
        return res

    @api.depends("sale_order_id")
    def _compute_sale_line_id(self):
        for wizard in self:
            if wizard.sale_line_id.order_id != wizard.sale_order_id:
                wizard.sale_line_id = False

    def _get_sale_line_move(self):
        self.ensure_one()
        moves = self.sale_line_id.get_delivery_move()
        if self.rma_id.picking_id:
            picking_moves = moves.filtered(
                lambda move: move.picking_id == self.rma_id.picking_id
            )
            moves = picking_moves or moves
        return moves[:1]

    def _prepare_rma_values(self):
        self.ensure_one()
        line = self.sale_line_id
        move = self._get_sale_line_move()
        vals = {
            "order_id": self.sale_order_id.id,
            "picking_id": False,
            "move_id": False,
            "product_id": line.product_id.id,
            "product_uom_qty": line.qty_delivered,
            "product_uom": line.product_uom.id,
        }
        if move:
            vals.update(
                {
                    "picking_id": move.picking_id.id,
                    "move_id": move.id,
                    "product_id": move.product_id.id,
                    "product_uom_qty": move.product_uom_qty,
                    "product_uom": move.product_uom.id,
                }
            )
        return vals

    def action_link_rma_to_sale_order(self):
        self.ensure_one()
        self.rma_id.write(self._prepare_rma_values())
        self.rma_id.message_post(
            body=_(
                "Sale Order %(order)s linked manually.", order=self.sale_order_id.name
            )
        )
