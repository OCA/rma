# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _prepare_rma_wizard_line_vals(self, data):
        vals = super()._prepare_rma_wizard_line_vals(data)
        vals["lot_id"] = data.get("lot_id")
        return vals
