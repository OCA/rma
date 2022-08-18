# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import _, fields, models


class RmaTeam(models.Model):
    _name = "rma.team"
    _inherit = ["mail.alias.mixin", "mail.thread"]
    _description = "RMA Team"
    _order = "sequence, name"

    sequence = fields.Integer()
    name = fields.Char(
        required=True,
        translate=True,
    )
    active = fields.Boolean(
        default=True,
        help="If the active field is set to false, it will allow you "
        "to hide the RMA Team without removing it.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Team Leader",
        domain=[("share", "=", False)],
        default=lambda self: self.env.user,
    )
    member_ids = fields.One2many(
        comodel_name="res.users",
        inverse_name="rma_team_id",
        string="Team Members",
    )

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if not default.get("name"):
            default["name"] = _("%s (copy)") % self.name
        team = super().copy(default)
        for follower in self.message_follower_ids:
            team.message_subscribe(
                partner_ids=follower.partner_id.ids,
                subtype_ids=follower.subtype_ids.ids,
            )
        return team

    def _alias_get_creation_values(self):
        values = super()._alias_get_creation_values()
        values["alias_model_id"] = self.env.ref("rma.model_rma").id
        if self.id:
            values["alias_defaults"] = defaults = ast.literal_eval(
                self.alias_defaults or "{}"
            )
            defaults["team_id"] = self.id
        return values
