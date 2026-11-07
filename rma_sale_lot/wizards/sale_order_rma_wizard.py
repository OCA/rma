# Copyright 2024 ACSONE SA/NV
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderRmaWizard(models.TransientModel):
    _inherit = "sale.order.rma.wizard"

    lots_visible = fields.Boolean(compute="_compute_lots_visible")

    @api.depends("line_ids.lots_visible")
    def _compute_lots_visible(self):
        for rec in self:
            rec.lots_visible = any(line.lots_visible for line in rec.line_ids)


class SaleOrderLineRmaWizard(models.TransientModel):
    _inherit = "sale.order.line.rma.wizard"

    lot_id_domain = fields.Binary(compute="_compute_lot_id_domain")
    lot_id = fields.Many2one(
        comodel_name="stock.lot", string="Lot/Serial Number", domain="lot_id_domain"
    )
    lots_visible = fields.Boolean(compute="_compute_lots_visible")

    @api.depends("move_id", "product_id")
    def _compute_lot_id_domain(self):
        for rec in self:
            smls = rec.move_id.move_line_ids.filtered(
                lambda x: x.state == "done" and x.lot_id
            )
            domain = [("id", "in", smls.lot_id.ids)]
            rec.lot_id_domain = domain

    @api.depends("product_id.tracking")
    def _compute_lots_visible(self):
        for rec in self:
            rec.lots_visible = rec.product_id.tracking != "none"

    def _prepare_rma_values(self):
        self.ensure_one()
        values = super()._prepare_rma_values()
        values["lot_id"] = self.lot_id.id
        return values
