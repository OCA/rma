# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    rma_kit_show_detailed = fields.Boolean(
        "RMA kit show detailed",
        help="If selected the rma wizard show's the kit move lines",
    )
