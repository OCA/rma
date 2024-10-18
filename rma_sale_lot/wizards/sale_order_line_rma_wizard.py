# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLineRmaWizard(models.TransientModel):

    _inherit = "sale.order.line.rma.wizard"

    lot_id = fields.Many2one(comodel_name="stock.lot", string="Lot/Serial Number")
    lots_visible = fields.Boolean(compute="_compute_lots_visible")

    @api.depends("product_id.tracking")
    def _compute_lots_visible(self):
        for rec in self:
            rec.lots_visible = rec.product_id.tracking != "none"

    def _prepare_rma_values(self):
        self.ensure_one()
        values = super()._prepare_rma_values()
        values["lot_id"] = self.lot_id.id
        return values
