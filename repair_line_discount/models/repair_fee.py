# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class RepairFee(models.Model):
    _inherit = "repair.fee"

    discount = fields.Float()

    @api.depends("price_unit", "repair_id", "product_uom_qty", "product_id", "discount")
    def _compute_price_subtotal(self):
        for fee in self:
            res = super()._compute_price_subtotal()
            fee.price_subtotal = fee.price_subtotal * (
                1 - (fee.discount or 0.0) / 100.0
            )
            return res
