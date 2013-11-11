# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion, 
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau, Joel Grand-Guillaume
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

    def _get_cleanup_fields(self, cr, uid, context=None):
        fields = super(account_invoice, self)._get_cleanup_fields(cr, uid, 
            context=context)
        fields = fields + ('claim_line_id',)
        return fields

    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        if context is None: context = {}
        new_lines = []
        # check if is an invoice_line
        if context.get('claim_line_ids') and lines and 'product_id' in lines[0]:
            for claim_line_id in context.get('claim_line_ids'):
                claim_info = self.pool.get('claim.line').read(cr, uid, 
                    claim_line_id[1], 
                    [
                        'invoice_line_id', 
                        'product_returned_quantity', 
                        'refund_line_id'], 
                    context=context)
                if not claim_info['refund_line_id']:
                    inv_line_obj = self.pool.get('account.invoice.line')
                    inv_line =  inv_line_obj.browse(cr, uid, 
                            [claim_info['invoice_line_id'][0]], 
                            context=context)[0]
                    clean_line = {}
                    for field in invoice_line_info._all_columns.keys():
                        column_type = inv_line._all_columns[field].column._type
                        if column_type == 'many2one':
                            clean_line[field] = inv_line[field].id
                        elif column_type not in ['many2many','one2many']:
                            clean_line[field] = inv_line[field]
                        elif field == 'invoice_line_tax_id':
                            tax_list = []
                            for tax in inv_line[field]:
                                tax_list.append(tax.id)
                            clean_line[field] = [(6,0, tax_list)]
                    clean_line['quantity'] = claim_info['product_returned_quantity']
                    clean_line['claim_line_id'] = [claim_line_id[1]]
                    new_lines.append(clean_line)
            if not new_lines:
                # TODO use custom states to show button of this wizard or 
                # not instead of raise an error
                raise osv.except_osv(_('Error !'), 
                    _('A refund has already been created for this claim !'))
        return map(lambda x: (0,0,x), new_lines)

    def _prepare_refund(self, cr, uid, *args, **kwargs):
        result = super(account_invoice, self)._prepare_refund(cr, uid, 
            *args, **kwargs)
        if kwargs.get('context') and kwargs['context'].get('claim_id'):
            result['claim_id'] = kwargs['context']['claim_id']
        return result

class account_invoice_line(orm.Model):

    _inherit = "account.invoice.line"

    def create(self, cr, uid, vals, context=None):
        claim_line_id = False
        if vals.get('claim_line_id'):
            claim_line_id = vals['claim_line_id']
            del vals['claim_line_id']
        line_id = super(account_invoice_line, self).create(cr, uid, 
            vals, context=context)
        if claim_line_id:
            claim_line_obj = self.pool.get('claim.line')
            claim_line_obj.write(cr, uid, claim_line_id, 
                {'refund_line_id': line_id}, context=context)
        return line_id
