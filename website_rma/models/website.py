# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    rma_default_team_id = fields.Many2one(
        comodel_name="rma.team",
        string="Default Team",
        help="Default team for new RMAs created through the 'Request RMA' form.",
    )
    rma_default_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Default Responsible",
        domain=[("share", "=", False)],
        help="Default responsible for new leads created through the "
        "'Request RMA' form.",
    )
