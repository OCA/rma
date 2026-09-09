# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class Rma(models.Model):
    _inherit = "rma"

    def _prepare_refund_line_vals(self):
        """
        If no sale order line associated to the RMA, use the variant price
        computed on pricelist.
        """
        result = super()._prepare_refund_line_vals()
        if not self.env.company.sudo().price_display_variant_pricelist_id:
            return result
        line = self.sudo().sale_line_id
        if not line and self.move_id.rma_id:
            # We use the RMA from which it was created
            line = self.move_id.rma_id.sudo().sale_line_id
        if not line:
            result["price_unit"] = self.product_id.pricelist_base_price
        return result
