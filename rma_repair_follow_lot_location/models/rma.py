# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):

    _inherit = "rma"

    def _get_repair_order_default_vals(self):
        self.ensure_one()
        vals = super()._get_repair_order_default_vals()
        vals[
            "default_follow_lot_location"
        ] = self.operation_id.repair_follow_lot_location
        return vals
