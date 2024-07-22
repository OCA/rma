# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):
    _name = "rma.operation"
    _description = "RMA requested operation"

    active = fields.Boolean(default=True)
    create_replacement_at_confirmation = fields.Boolean(
        help="Create the replacement picking upon confirmation."
    )
    name = fields.Char(required=True, translate=True)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "That operation name already exists !"),
    ]
