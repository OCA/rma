# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    rma_delivery_strategy = fields.Selection(
        selection=[
            ("fixed_method", "Fixed method"),
            ("customer_method", "Customer method"),
            ("mixed_method", "Customer method (fallback to fixed)"),
        ],
        string="RMA delivery method strategy",
        default="mixed_method",
    )
    rma_fixed_delivery_method = fields.Many2one(
        comodel_name="delivery.carrier", string="Default RMA delivery method",
    )
