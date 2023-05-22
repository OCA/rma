# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

TIMING_REFUND_SO = "update_sale_delivered_qty"


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    create_refund_timing = fields.Selection(
        selection_add=[(TIMING_REFUND_SO, "Update SO delivered qty")]
    )
