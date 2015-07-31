# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Eezee-It
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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

from openerp.models import Model, api, _
from openerp import fields


class AccountInvoice(Model):
    _inherit = "account.invoice"

    claim_id = fields.Many2one('crm.claim', string='Claim')

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Override when from claim to update the quantity and link to the
        claim line."""
        new_lines = []
        inv_line_obj = self.env['account.invoice.line']
        claim_line_obj = self.env['claim.line']

        # check if is an invoice_line and we are from a claim
        if not (self.env.context.get('claim_line_ids') and lines and
                lines[0]._name == 'account.invoice.line'):
            return super(AccountInvoice, self)._refund_cleanup_lines(lines)

        for __, claim_line_id, __ in self.env.context.get('claim_line_ids'):
            line = claim_line_obj.browse(claim_line_id)
            if not line.refund_line_id:
                # For each lines replace quantity and add claim_line_id
                inv_line = inv_line_obj.browse(line.invoice_line_id.id)
                clean_line = {}
                for field_name, field in inv_line._all_columns.iteritems():
                    column_type = field.column._type
                    if column_type == 'many2one':
                        clean_line[field_name] = inv_line[field_name].id
                    elif column_type not in ('many2many', 'one2many'):
                        clean_line[field_name] = inv_line[field_name]
                    elif field_name == 'invoice_line_tax_id':
                        tax_list = []
                        for tax in inv_line[field_name]:
                            tax_list.append(tax.id)
                        clean_line[field_name] = [(6, 0, tax_list)]
                clean_line['quantity'] = line['product_returned_quantity']
                clean_line['claim_line_id'] = [claim_line_id]
                new_lines.append(clean_line)
        if not new_lines:
            # TODO use custom states to show button of this wizard or
            # not instead of raise an error
            raise Warning(
                _('A refund has already been created for this claim !'))
        return [(0, 0, l) for l in new_lines]

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        result = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id, description=description,
            journal_id=journal_id)

        if self.env.context.get('claim_id'):
            result['claim_id'] = self.env.context.get('claim_id')

        return result


class AccountInvoiceLine(Model):
    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        claim_line_id = False
        if vals.get('claim_line_id'):
            claim_line_id = vals['claim_line_id']
            del vals['claim_line_id']

        line_id = super(AccountInvoiceLine, self).create(vals)
        if claim_line_id:
            claim_line = self.env['claim.line'].browse(claim_line_id)
            claim_line.write({'refund_line_id': line_id.id})

        return line_id
