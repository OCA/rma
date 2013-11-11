# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Raphaël Valyi, Sébastien Beau, 	#
# Emmanuel Samyn, Benoît Guillot                                        #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields, osv
from tools.translate import _

class account_invoice(osv.osv):

    _inherit = "account.invoice"


    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }

    def _get_cleanup_fields(self, cr, uid, context=None):
        fields = super(account_invoice, self)._get_cleanup_fields(cr, uid, context=context)
        fields = fields + ('claim_line_id',)
        return fields

    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        if context is None: context = {}
        new_lines = []
        if context.get('claim_line_ids') and lines and 'product_id' in lines[0]:#check if is an invoice_line
            for claim_line_id in context.get('claim_line_ids'):
                claim_info = self.pool.get('claim.line').read(cr, uid, claim_line_id[1], ['invoice_line_id', 'product_returned_quantity', 'refund_line_id'], context=context)
                if not claim_info['refund_line_id']:
                    invoice_line_info =  self.pool.get('account.invoice.line').browse(cr, uid, [claim_info['invoice_line_id'][0]], context=context)[0]
                    clean_line = {}
                    for field in invoice_line_info._all_columns.keys():
                        if invoice_line_info._all_columns[field].column._type == 'many2one':
                            clean_line[field] = invoice_line_info[field].id
                        elif invoice_line_info._all_columns[field].column._type not in ['many2many','one2many']:
                            clean_line[field] = invoice_line_info[field]
                        elif field == 'invoice_line_tax_id':
                            tax_list = []
                            for tax in invoice_line_info[field]:
                                tax_list.append(tax.id)
                            clean_line[field] = [(6,0, tax_list)]
                    #invoice_line_info = self.pool.get('account.invoice.line').read(cr, uid, claim_info['invoice_line_id'][0], context=context)
                    clean_line['quantity'] = claim_info['product_returned_quantity']
                    clean_line['claim_line_id'] = [claim_line_id[1]]
                    new_lines.append(clean_line)
            if not new_lines:
                #TODO use custom states to show button of this wizard or not instead of raise an error
                raise osv.except_osv(_('Error !'), _('A refund has already been created for this claim !'))
        #result = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines, context=context)
        return map(lambda x: (0,0,x), new_lines)

    def _prepare_refund(self, cr, uid, *args, **kwargs):
        result = super(account_invoice, self)._prepare_refund(cr, uid, *args, **kwargs)
        if kwargs.get('context') and kwargs['context'].get('claim_id'):
            result['claim_id'] = kwargs['context']['claim_id']
        return result

class account_invoice_line(osv.osv):

    _inherit = "account.invoice.line"

    def create(self, cr, uid, vals, context=None):
        claim_line_id = False
        if vals.get('claim_line_id'):
            claim_line_id = vals['claim_line_id']
            del vals['claim_line_id']
        line_id = super(account_invoice_line, self).create(cr, uid, vals, context=context)
        if claim_line_id:
            self.pool.get('claim.line').write(cr, uid, claim_line_id, {'refund_line_id': line_id}, context=context)
        return line_id
