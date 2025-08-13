# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    deliver_same_lot = fields.Boolean(
        string="Deliver Same Lot/Serial as Received",
        help="If enabled, the replacement or delivery product will use the exact "
        "lot/serial number received from the customer. Disable if a different "
        "lot or serial number should be assigned.",
    )
