# Copyright 2024 Raumschmiede GmbH
# Copyright 2024 BCIM
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    is_rma_reason_required = fields.Boolean(
        string="Indicates whether specifying an RMA reason is mandatory when creating "
        "an RMA order."
    )
