# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rma_delivery_strategy = fields.Selection(
        related="company_id.rma_delivery_strategy", readonly=False,
    )
    rma_fixed_delivery_method = fields.Many2one(
        related="company_id.rma_fixed_delivery_method", readonly=False,
    )
