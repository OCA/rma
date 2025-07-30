# Copyright 2021 Tecnativa - David Vidal
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_rma_invoice_lines_qty(self):
        """For those with differences, check if the kit quantity is the same"""
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        lines = super()._check_rma_invoice_lines_qty()
        if lines:
            return lines.sudo().filtered(
                lambda r: (
                    not r.rma_id.phantom_bom_product
                    or r.rma_id.phantom_bom_product
                    and float_compare(r.quantity, r.rma_id.kit_qty, precision) < 0
                )
            )
        return lines
