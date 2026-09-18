# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_full_page_sale_rma = fields.Boolean(
        related="company_id.show_full_page_sale_rma",
        readonly=False,
    )
