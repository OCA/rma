# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = "res.company"

    def _default_rma_mail_confirmation_template(self):
        try:
            return self.env.ref("rma.mail_template_rma_notification").id
        except ValueError:
            return False

    send_rma_confirmation = fields.Boolean(
        string="Send RMA Confirmation",
        help="When the delivery is confirmed, send a confirmation email "
             "to the customer.",
    )
    rma_mail_confirmation_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template confirmation for RMA",
        domain="[('model', '=', 'rma')]",
        default=_default_rma_mail_confirmation_template,
        help="Email sent to the customer once the RMA is confirmed.",
    )

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        company.create_rma_index()
        return company

    def create_rma_index(self):
        return self.env['ir.sequence'].sudo().create({
            'name': _('RMA Code'),
            'prefix': 'RMA',
            'code': 'rma',
            'padding': 4,
            'company_id': self.id,
        })
