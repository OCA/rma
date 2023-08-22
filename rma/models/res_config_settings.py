# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_rma_manual_finalization = fields.Boolean(
        string="Finish RMA manually choosing a reason",
        help="Allow to finish an RMA without returning back a product or refunding",
        implied_group="rma.group_rma_manual_finalization",
    )
    rma_return_grouping = fields.Boolean(
        related="company_id.rma_return_grouping",
        readonly=False,
    )
    send_rma_confirmation = fields.Boolean(
        related="company_id.send_rma_confirmation",
        readonly=False,
    )
    rma_mail_confirmation_template_id = fields.Many2one(
        related="company_id.rma_mail_confirmation_template_id",
        readonly=False,
    )
    send_rma_receipt_confirmation = fields.Boolean(
        related="company_id.send_rma_receipt_confirmation",
        readonly=False,
    )
    rma_mail_receipt_confirmation_template_id = fields.Many2one(
        related="company_id.rma_mail_receipt_confirmation_template_id",
        readonly=False,
    )
    send_rma_draft_confirmation = fields.Boolean(
        related="company_id.send_rma_draft_confirmation",
        readonly=False,
    )
    rma_mail_draft_confirmation_template_id = fields.Many2one(
        related="company_id.rma_mail_draft_confirmation_template_id",
        readonly=False,
    )
