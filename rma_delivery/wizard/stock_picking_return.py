# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_rma_vals(self):
        vals = super()._prepare_rma_vals()
        if self.wizard_id.reception_carrier_id:
            vals["reception_carrier_id"] = self.wizard_id.reception_carrier_id.id
        return vals


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    reception_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Reception Carrier",
    )
    rma_reception_strategy = fields.Selection(
        related="picking_id.company_id.rma_reception_strategy"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "picking_id" in res and "reception_carrier_id" in fields:
            picking = self.env["stock.picking"].browse(res.get("picking_id"))
            if picking.company_id.rma_reception_strategy == "rma_method":
                res["reception_carrier_id"] = picking.carrier_id.id
        return res
