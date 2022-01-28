# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RmaFinalization(models.Model):
    _description = "RMA Finalization Reason"
    _name = "rma.finalization"
    _order = "name"

    active = fields.Boolean(default=True)
    name = fields.Char(
        string="Reason Name",
        required=True,
        translate=True,
        copy=False,
    )
    company_id = fields.Many2one(comodel_name="res.company")

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, company_id)",
            "Finalization name already exists !",
        ),
    ]
