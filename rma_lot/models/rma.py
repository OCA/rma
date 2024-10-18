# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Rma(models.Model):
    _inherit = "rma"

    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial Number",
        domain="[('product_id', '=?', product_id)]",
        compute="_compute_lot_id",
        store=True,
        readonly=False,
    )
    lots_visible = fields.Boolean(compute="_compute_lots_visible")

    @api.depends("product_id.tracking")
    def _compute_lots_visible(self):
        for rec in self:
            rec.lots_visible = rec.product_id.tracking != "none"

    def _prepare_reception_procurement_vals(self, group=None):
        vals = super()._prepare_reception_procurement_vals(group=group)
        vals["restrict_lot_id"] = self.lot_id.id
        return vals

    @api.depends("move_id", "lot_id")
    def _compute_product_id(self):
        res = super()._compute_product_id()
        for rec in self:
            if not rec.move_id and rec.lot_id:
                self.product_id = rec.lot_id.product_id
        return res

    @api.depends("product_id")
    def _compute_lot_id(self):
        self.update({"lot_id": False})
