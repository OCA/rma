# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    return_eligibility_days = fields.Integer(
        string="Return eligibility duration (days)",
        help=(
            "Defines the time window in which sales can be linked "
            "automatically to RMA lines. "
            "Example: 30 days (change of mind), 730 days (warranty), "
            "0 to disable, or a large number for lifetime warranty."
        ),
        default=30,
    )
    return_eligibility_order = fields.Selection(
        selection=[("older_first", "Older First"), ("recent_first", "Recent First")],
        help="This will change the way of eligible sale orders are retrieved.",
        required=True,
        default="older_first",
    )
