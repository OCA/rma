# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    rma_team_id = fields.Many2one(
        comodel_name="rma.team",
        string="RMA Team",
        help="RMA Team the user is member of.",
    )
