# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):

    _inherit = "rma"

    def _get_repair_order_default_vals(self):
        self.ensure_one()
        vals = super()._get_repair_order_default_vals()
        if self.operation_id.repair_warehouse_id:
            vals["default_warehouse_id"] = self.operation_id.repair_warehouse_id.id
        if self.operation_id.repair_location_id:
            vals["default_location_id"] = self.operation_id.repair_location_id.id
        return vals
