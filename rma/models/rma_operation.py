# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):
    _name = "rma.operation"
    _description = "RMA requested operation"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    prevent_delivery_grouping = fields.Boolean(
        string="Do not group deliveries",
        help="If enabled, RMAs using this operation will NOT be grouped into a "
        "single delivery picking, even if the company setting allows grouping.",
    )
    _sql_constraints = [
        ("name_uniq", "unique (name)", "That operation name already exists !"),
    ]
