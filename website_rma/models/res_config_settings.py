# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rma_default_team_id = fields.Many2one(
        comodel_name="rma.team",
        related="website_id.rma_default_team_id",
        readonly=False,
    )
    rma_default_user_id = fields.Many2one(
        comodel_name="res.users",
        related="website_id.rma_default_user_id",
        readonly=False,
        help="Default responsible for new leads created through the "
        "'Request RMA' form.",
    )
