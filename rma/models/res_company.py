# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _default_rma_mail_confirmation_template(self):
        try:
            return self.env.ref("rma.mail_template_rma_notification").id
        except ValueError:
            return False

    def _default_rma_mail_receipt_template(self):
        try:
            return self.env.ref("rma.mail_template_rma_receipt_notification").id
        except ValueError:
            return False

    def _default_rma_mail_draft_template(self):
        try:
            return self.env.ref("rma.mail_template_rma_draft_notification").id
        except ValueError:
            return False

    rma_return_grouping = fields.Boolean(
        string="Group RMA returns by customer address and warehouse",
        default=True,
    )
    send_rma_confirmation = fields.Boolean(
        string="Send RMA Confirmation",
        help="When the delivery is confirmed, send a confirmation email "
        "to the customer.",
    )
    send_rma_receipt_confirmation = fields.Boolean(
        string="Send RMA Receipt Confirmation",
        help="When the RMA receipt is confirmed, send a confirmation email "
        "to the customer.",
    )
    send_rma_draft_confirmation = fields.Boolean(
        string="Send RMA draft Confirmation",
        help="When a customer places an RMA, send a notification with it",
    )
    rma_mail_confirmation_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template confirmation for RMA",
        domain="[('model', '=', 'rma')]",
        default=_default_rma_mail_confirmation_template,
        help="Email sent to the customer once the RMA is confirmed.",
    )
    rma_mail_receipt_confirmation_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template receipt confirmation for RMA",
        domain="[('model', '=', 'rma')]",
        default=_default_rma_mail_receipt_template,
        help="Email sent to the customer once the RMA products are received.",
    )
    rma_mail_draft_confirmation_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template draft notification for RMA",
        domain="[('model', '=', 'rma')]",
        default=_default_rma_mail_draft_template,
        help="Email sent to the customer when they place " "an RMA from the portal",
    )

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            company.create_rma_index()
        return companies

    def create_rma_index(self):
        return (
            self.env["ir.sequence"]
            .sudo()
            .create(
                {
                    "name": _("RMA Code"),
                    "prefix": "RMA",
                    "code": "rma",
                    "padding": 4,
                    "company_id": self.id,
                }
            )
        )
