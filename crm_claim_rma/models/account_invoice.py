# -*- coding: utf-8 -*-
# © 2019 Versada UAB
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import itertools

from odoo import _, api, exceptions, fields, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    claim_id = fields.Many2one('crm.claim', string='Claim')

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Override when from claim to update the quantity, link to the
        claim line and return empty list for tax_line_ids.
        """
        claim_lines_context = self.env.context.get('claim_line_ids')

        if not (lines and claim_lines_context):
            return super(AccountInvoice, self)._refund_cleanup_lines(lines)

        # We don't want tax_line_ids from origin invoice as new ones
        # will be calculated for correct number of lines

        if lines[0]._name == 'account.invoice.tax':
            return []

        claim_lines = self.env['claim.line'].browse([l[1] for l in claim_lines_context])
        claim_lines_wo_refund = claim_lines.filtered(
            lambda s: not s.refund_line_id).sorted('invoice_line_id')

        if not claim_lines_wo_refund:

            raise exceptions.UserError(
                _('A refund has already been created for all lines on this claim !')
            )

        # _refund_cleanup_lines keep original sequence so instead of C/P Odoo code
        #  we can sort record set and update create values.

        invoice_lines = claim_lines_wo_refund.mapped('invoice_line_id').sorted()

        # data from res in format (0, 0, {field:value})
        refund_invoice_lines_data = super(
            AccountInvoice, self)._refund_cleanup_lines(invoice_lines)

        for claim_line, invoice_create_values in itertools.izip(
                claim_lines_wo_refund,
                refund_invoice_lines_data):

            create_values = invoice_create_values[2]
            create_values.update(
                quantity=claim_line.product_returned_quantity,
                claim_line_id=claim_line.id,
            )
        return refund_invoice_lines_data

    @api.model
    def _prepare_refund(self, *args, **kwargs):
        result = super(AccountInvoice, self)._prepare_refund(*args, **kwargs)

        if self.env.context.get('claim_id'):
            result['claim_id'] = self.env.context['claim_id']

        return result
