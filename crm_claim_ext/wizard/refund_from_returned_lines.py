# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn                     #
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
import pooler
import time

class refund_from_returned_lines(osv.osv_memory):
    _name='refund_from_returned_lines.wizard'
    _description='Wizard to create an refund for selected product return lines'
    _columns = {
        'refund_journal' : fields.many2one('account.journal', 'Refund journal', select=True),
        'claim_line_ids' : fields.many2many('temp.claim.line', string='Selected return lines'),
    }

    # Get selected lines to add to picking in
    def _get_selected_lines(self, cr, uid,context):
        returned_line_ids = self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['claim_line_ids'])['claim_line_ids'] 
        returned_lines = self.pool.get('claim.line').browse(cr, uid,returned_line_ids)
        M2M = []
        for line in returned_lines:
            if True: #line.selected:
                M2M.append(self.pool.get('temp.claim.line').create(cr, uid, {
                        'claim_origine' : "none",
                        'invoice_id' : line.invoice_id.id,
                        'product_id' : line.product_id.id,
                        'product_returned_quantity' : line.product_returned_quantity,
                        'prodlot_id' : line.prodlot_id.id,
                        'price_unit' :  line.unit_sale_price,
                    }))
        return M2M

    # Get default journal
    def _get_journal(self, cr, uid,context):
        #('company_id','=',claim_id.company_id.id)
        # ,('refund_journal','=','True')
        return self.pool.get('account.journal').search(cr, uid, [('type','=','sale_refund')],limit=1)[0] 

    _defaults = {
        'claim_line_ids': _get_selected_lines,
        'refund_journal' : _get_journal,
    }

    # On "Cancel" button
    def action_cancel(self,cr,uid,ids,context=None):
        return {'type': 'ir.actions.act_window_close',}

    # On "Create" button
    def action_create_refund(self, cr, uid, ids, context=None):
        partner_id = 0
        for refund in self.browse(cr, uid,ids):
            claim_id = self.pool.get('crm.claim').browse(cr, uid, context['active_id'])
            partner_id = claim_id.partner_id.id
            # invoice type
            invoice_type = "out_refund"
            if claim_id.claim_type == "supplier":
                invoice_type = "in_refund"
            # create invoice
            invoice_id = self.pool.get('account.invoice').create(cr, uid, {
                        'claim_origine' : "none",
                        'origin' : claim_id.sequence,
                        'type' : invoice_type,
                        'state' : 'draft',
                        'partner_id' : claim_id.partner_id.id,
                        'user_id' : uid,
                        'reference_type': 'none',
                        'date_invoice': time.strftime('%Y-%m-%d %H:%M:%S'),
                        # 'date_due':
                        'partner_id' : claim_id.partner_id.id,
                        'commercial_partner_id' : claim_id.partner_id.id,
                        'account_id' : claim_id.partner_id.property_account_receivable.id,
                        'currency_id' : claim_id.company_id.currency_id.id, # from invoice ???
                        'journal_id' : refund.refund_journal.id,
                        'company_id' : claim_id.company_id.id,
                        'comment' : 'RMA Refund',
                        'claim_id': claim_id.id,
                    })
            # Create invoice lines
            for refund_line in refund.claim_line_ids:
                if refund_line.invoice_id:
                    invoice_line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                        'name' : refund_line.product_id.name_template,
                        'origin' : claim_id.sequence,
                        'invoice_id' : invoice_id,
                        'uos_id' : refund_line.product_id.uom_id.id,
                        'product_id':refund_line.product_id.id,
                        'account_id': claim_id.partner_id.property_account_receivable.id, # refund_line.product_id.property_account_expense.id,
                        'price_unit':refund_line.price_unit,
                        'quantity': refund_line.product_returned_quantity,
#                        'discount':
#                        'invoice_line_tax_id':
#                        'account_analytic_id':
                        'company_id' : claim_id.company_id.id,
                        'partner_id' : refund_line.invoice_id.partner_id.id,
                        'note': 'RMA Refund',
                        })
                else:
                    raise osv.except_osv(_('Error !'), _('Cannot find any invoice for the return line!'))
        return {
            'name': 'Customer Refounds',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain' : "[('type', '=', '"+invoice_type+"'),('partner_id','=',"+str(partner_id)+")]",
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
        }

refund_from_returned_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
