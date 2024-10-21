# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):
    _name = "rma.operation"
    _description = "RMA requested operation"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    action_create_receipt = fields.Selection(
        [
            ("manual_on_confirm", "Manually on Confirm"),
            ("automatic_on_confirm", "Automatically on Confirm"),
        ],
        string="Create Receipt",
        default="automatic_on_confirm",
        help="Define how the receipt action should be handled.",
    )
    different_return_product = fields.Boolean(
        help="If checked, allows the return of a product different from the one "
        "originally ordered. Used if the delivery is created automatically",
    )
    action_create_delivery = fields.Selection(
        [
            ("manual_on_confirm", "Manually on Confirm"),
            ("automatic_on_confirm", "Automatically on Confirm"),
            ("manual_after_receipt", "Manually After Receipt"),
            ("automatic_after_receipt", "Automatically After Receipt"),
        ],
        string="Delivery Action",
        help="Define how the delivery action should be handled.",
        default="manual_after_receipt",
    )
    action_create_refund = fields.Selection(
        [
            ("manual_on_confirm", "Manually on Confirm"),
            ("automatic_on_confirm", "Automatically on Confirm"),
            ("manual_after_receipt", "Manually After Receipt"),
            ("automatic_after_receipt", "Automatically After Receipt"),
            ("update_quantity", "Update Quantities"),
        ],
        string="Refund Action",
        default="manual_after_receipt",
        help="Define how the refund action should be handled.",
    )

    _sql_constraints = [
        ("name_uniq", "unique (name)", "That operation name already exists !"),
    ]
