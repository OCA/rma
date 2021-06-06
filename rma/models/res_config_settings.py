# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    send_rma_confirmation = fields.Boolean(
        related="company_id.send_rma_confirmation",
        readonly=False,
    )
    rma_mail_confirmation_template_id = fields.Many2one(
        related="company_id.rma_mail_confirmation_template_id",
        readonly=False,
    )
