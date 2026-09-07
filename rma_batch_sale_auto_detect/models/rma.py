# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):
    _inherit = "rma"

    def _onchange_order_id(self):
        # allow user to select product then so in batch view
        if not self.env.context.get("ignore_onchange_order_id", False):
            return super()._onchange_order_id()
        return {}
