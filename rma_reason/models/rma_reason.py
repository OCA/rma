# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaReason(models.Model):

    _name = "rma.reason"
    _description = "Rma Reason"

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
