# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It, MONK Software, Vauxoo
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume, Leonardo Donelli
#            Osval Reyes, Yanina Aular
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import _, api, exceptions, fields, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    claim_id = fields.Many2one('crm.claim', string='Claim')

    @api.model
    def _refund_cleanup_lines(self, lines):
        """
        Override when from claim to update the quantity and link to the
        claim line.
        """

        # check if is an invoice_line and we are from a claim
        if not (self.env.context.get('claim_line_ids') and lines and
                lines[0]._name == 'account.invoice.line'):
            return super(AccountInvoice, self)._refund_cleanup_lines(lines)

        # start by browsing all the lines so that Odoo will correctly prefetch
        line_ids = [l[1] for l in self.env.context['claim_line_ids']]
        claim_lines = self.env['claim.line'].browse(line_ids)

        new_lines = []
        for claim_line in claim_lines:
            if not claim_line.refund_line_id:
                # For each lines replace quantity and add claim_line_id
                inv_line = claim_line.invoice_line_id
                clean_line = {}
                for field_name, field in inv_line._all_columns.iteritems():
                    column_type = field.column._type
                    if column_type == 'many2one':
                        clean_line[field_name] = inv_line[field_name].id
                    elif column_type not in ('many2many', 'one2many'):
                        clean_line[field_name] = inv_line[field_name]
                    elif field_name == 'invoice_line_tax_id':

                        tax_ids = inv_line[field_name].ids
                        clean_line[field_name] = [(6, 0, tax_ids)]
                clean_line['quantity'] = claim_line.product_returned_quantity
                clean_line['claim_line_id'] = [claim_line.id]

                new_lines.append(clean_line)
        if not new_lines:
            # TODO use custom states to show button of this wizard or
            # not instead of raise an error

            raise exceptions.Warning(
                _('A refund has already been created for this claim !'))
        return [(0, 0, l) for l in new_lines]

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        result = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id, description=description,
            journal_id=journal_id)

        if self.env.context.get('claim_id'):
            result['claim_id'] = self.env.context['claim_id']

        return result
