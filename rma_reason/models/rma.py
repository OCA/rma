# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Rma(models.Model):

    _inherit = "rma"

    reason_id = fields.Many2one(comodel_name="rma.reason")
    is_rma_reason_required = fields.Boolean(related="company_id.is_rma_reason_required")
