# -*- coding: utf-8 -*-
##############################################################################
#
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
from openerp.osv import fields, orm
from tools.translate import _


class account_invoice(orm.Model):

    _inherit = "account.invoice"

    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }

    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        """ Override when from claim to update the quantity and link to the
        claim line."""
        if context is None:
            context = {}
        new_lines = []
        inv_line_obj = self.pool.get('account.invoice.line')
        claim_line_obj = self.pool.get('claim.line')
        # check if is an invoice_line and we are from a claim
        if not (context.get('claim_line_ids') and lines and
                lines[0]._name == 'account.invoice.line'):
            return super(account_invoice, self)._refund_cleanup_lines(
                cr, uid, lines, context=None)

        for __, claim_line_id, __ in context.get('claim_line_ids'):
            line = claim_line_obj.browse(cr, uid, claim_line_id,
                                         context=context)
            if not line.refund_line_id:
                # For each lines replace quantity and add claim_line_id
                inv_line = inv_line_obj.browse(cr, uid,
                                               line.invoice_line_id.id,
                                               context=context)
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
            raise orm.except_orm(
                _('Error !'),
                _('A refund has already been created for this claim !'))
        return [(0, 0, l) for l in new_lines]

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None,
                        description=None, journal_id=None, context=None):
        if context is None:
            context = {}
        result = super(account_invoice, self)._prepare_refund(
            cr, uid, invoice,
            date=date, period_id=period_id, description=description,
            journal_id=journal_id, context=context)
        if context.get('claim_id'):
            result['claim_id'] = context['claim_id']
        return result


class account_invoice_line(orm.Model):

    _inherit = "account.invoice.line"

    def create(self, cr, uid, vals, context=None):
        claim_line_id = False
        if vals.get('claim_line_id'):
            claim_line_id = vals['claim_line_id']
            del vals['claim_line_id']
        line_id = super(account_invoice_line, self).create(
            cr, uid, vals, context=context)
        if claim_line_id:
            claim_line_obj = self.pool.get('claim.line')
            claim_line_obj.write(cr, uid, claim_line_id,
                                 {'refund_line_id': line_id},
                                 context=context)
        return line_id
