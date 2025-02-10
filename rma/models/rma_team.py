# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import fields, models


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
        default = dict(default or {})
        new_teams = super().copy(default)
        for old_team, new_team in zip(self, new_teams, strict=False):
            if not default.get("name"):
                new_team.name = self.env._("%s (copy)") % old_team.name
            for follower in old_team.message_follower_ids:
                new_team.message_subscribe(
                    partner_ids=follower.partner_id.ids,
                    subtype_ids=follower.subtype_ids.ids,
                )
        return new_teams

    def _alias_get_creation_values(self):
        values = super()._alias_get_creation_values()
        values["alias_model_id"] = self.env.ref("rma.model_rma").id
        if self.id:
            values["alias_defaults"] = defaults = ast.literal_eval(
                self.alias_defaults or "{}"
            )
            defaults["team_id"] = self.id
        return values
