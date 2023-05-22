# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

TIMING_ON_CONFIRM = "on_confirm"
TIMING_AFTER_RECEIPT = "after_receipt"
TIMING_NO = "no"

TIMING_ON_CONFIRM_STR = "On confirm"
TIMING_AFTER_RECEIPT_STR = "After receipt"


class RmaOperation(models.Model):
    _name = "rma.operation"
    _description = "RMA requested operation"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)

    create_receipt_timing = fields.Selection(
        [
            (TIMING_ON_CONFIRM, TIMING_ON_CONFIRM_STR),
            (TIMING_NO, "No receipt"),
        ],
        "Receipt timing",
        default=TIMING_ON_CONFIRM,
    )

    create_return_timing = fields.Selection(
        [
            (TIMING_ON_CONFIRM, TIMING_ON_CONFIRM_STR),
            (TIMING_AFTER_RECEIPT, TIMING_AFTER_RECEIPT_STR),
            (TIMING_NO, "No Return"),
        ],
        "Delivery timing",
        default=TIMING_AFTER_RECEIPT,
    )

    create_refund_timing = fields.Selection(
        [
            (TIMING_ON_CONFIRM, TIMING_ON_CONFIRM_STR),
            (TIMING_AFTER_RECEIPT, TIMING_AFTER_RECEIPT_STR),
            (TIMING_NO, "No refund"),
        ],
        "Refund timing",
        default=TIMING_AFTER_RECEIPT,
    )

    _sql_constraints = [
        ("name_uniq", "unique (name)", "That operation name already exists !"),
    ]
