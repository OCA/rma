# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Rma(models.Model):
    _inherit = "rma"

    def website_form_input_filter(self, request, values):
        values.update(
            team_id=values.get("team_id") or request.website.rma_default_team_id.id,
            user_id=values.get("user_id") or request.website.rma_default_user_id.id,
            partner_id=values.get("partner_id") or request.env.user.partner_id.id,
            origin="Website form",
        )
        return values
