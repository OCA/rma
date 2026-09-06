# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RestockingFeeMixin(models.AbstractModel):
    _name = "restocking.fee.mixin"
    _description = "Restocking Fee Mixin"

    restocking_fee_type = fields.Selection(
        [
            ("fixed", "Fixed Amount"),
            ("percent", "Percentage"),
        ],
        help="Define whether the restocking fee is a fixed amount or a percentage.",
    )

    restocking_fee_amount = fields.Float()

    @api.constrains("restocking_fee_type", "restocking_fee_amount")
    def _check_restocking_fee_amount(self):
        for rec in self:
            if not rec.restocking_fee_type:
                continue
            if rec.restocking_fee_amount <= 0:
                raise ValidationError(
                    _("Restocking fee amount must be greater than zero.")
                )
            if rec.restocking_fee_type == "percent":
                if rec.restocking_fee_amount > 100:
                    raise ValidationError(
                        _("Restocking fee percentage cannot exceed 100%.")
                    )
