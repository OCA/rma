# -*- coding: utf-8 -*-
# © 2015 Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        claim_line_id = vals.get('claim_line_id')
        if claim_line_id:
            del vals['claim_line_id']

        line = super(AccountInvoiceLine, self).create(vals)
        if claim_line_id:
            claim_line = self.env['claim.line'].browse(claim_line_id)
            claim_line.refund_line_id = line.id

        return line
