# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    create_rma_at_confirm = fields.Boolean()
    rma_create_operation_id = fields.Many2one(
        comodel_name="rma.operation",
    )

    @api.constrains("rma_create_operation_id")
    def _check_rma_create_operation_id(self):
        for record in self:
            if record.create_rma_at_confirm and not record.rma_create_operation_id:
                self.env._(
                    "If you enable RMA creation at picking validation, you need to fill"
                    " in the default operation."
                )
