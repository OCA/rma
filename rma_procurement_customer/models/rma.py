# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):

    _inherit = "rma"

    def _prepare_procurement_group_vals(self):
        res = super()._prepare_procurement_group_vals()
        if self.move_id.picking_id.customer_id:
            res["customer_id"] = self.move_id.picking_id.customer_id.id
        return res
