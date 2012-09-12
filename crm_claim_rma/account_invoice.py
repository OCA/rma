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

class account_invoice(osv.osv):

    _inherit = "account.invoice"


    _columns = {
        'claim_id': fields.many2one('crm.claim', 'Claim'),
    }

    def _refund_cleanup_lines(self, cr, uid, lines, context=None):
        new_lines = []
        if context.get('claim_line_ids') and lines and 'product_id' in lines[0]:#check if is an invoice_line
            for claim_line_id in context.get('claim_line_ids'):
                claim_info = self.pool.get('claim.line').read(cr, uid, claim_line_id[1], ['invoice_line_id', 'product_returned_quantity'], context=context)
                invoice_line_info = self.pool.get('account.invoice.line').read(cr, uid, claim_info['invoice_line_id'][0], context=context)
                invoice_line_info['quantity'] = claim_info['product_returned_quantity']
                new_lines.append(invoice_line_info)
            lines = new_lines
        result = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines, context=context)
        return result

    def _prepare_refund(self, cr, uid, *args, **kwargs):
        result = super(account_invoice, self)._prepare_refund(cr, uid, *args, **kwargs)
        if kwargs.get('context') and kwargs['context'].get('claim_id'):
            result['claim_id'] = kwargs['context']['claim_id']
        return result
