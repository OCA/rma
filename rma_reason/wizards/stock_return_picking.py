# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReturnPicking(models.TransientModel):

    _inherit = "stock.return.picking"

    rma_reason_id = fields.Many2one(
        comodel_name="rma.reason", readonly=False, string="RMA Reason"
    )
