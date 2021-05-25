# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RmaTag(models.Model):
    _description = "RMA Tags"
    _name = "rma.tag"
    _order = "name"

    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide the category without " "removing it.",
    )
    name = fields.Char(
        string="Tag Name",
        required=True,
        translate=True,
        copy=False,
    )
    is_public = fields.Boolean(
        string="Public Tag",
        help="The tag is visible in the portal view",
    )
    color = fields.Integer(string="Color Index")
    rma_ids = fields.Many2many(comodel_name="rma")

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Tag name already exists !"),
    ]
