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
#import time
#from datetime import datetime
#from dateutil.relativedelta import relativedelta

#===== WIZ STEP 1 : Invoice selection
class returned_lines_from_invoice_invoice(osv.osv_memory):
    _name='returned_lines_from_invoice_invoice.wizard'
    _description='Wizard to create product return lines from invoice'
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }
    
    # Get partner from case is set
    def _get_default_partner_id(self, cr, uid, context):
        return self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['partner_id'])['partner_id']

    _defaults = {
        'partner_id': _get_default_partner_id,
    }

    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}   
        
    # If "Return all" button pressed
    def action_return_all(self, cr, uid, ids, context):
        # Get invoice id
        inv_id = 0
        for wiz_obj in self.browse(cr,uid,ids):
            inv_id = wiz_obj.invoice_id.id
        # Get invoice line ids from invoice id
        invoice_line_pool = self.pool.get('account.invoice.line')
        invoice_lines_ids = invoice_line_pool.search(cr, uid, [('invoice_id', '=', inv_id)])       
        # Get invoice lines from invoice line ids
        for invoice_line in invoice_line_pool.browse(cr,uid,invoice_lines_ids):
            claim_line_pool = self.pool.get('claim.line')
            line_id = claim_line_pool.create(cr, uid, {
					'claim_origine' : "none",
					'invoice_id' : invoice_line.invoice_id.id,
					'product_id' : invoice_line.product_id.id,
					'product_returned_quantity' : invoice_line.quantity,
					'unit_sale_price' : invoice_line.price_unit,
					#'prodlot_id' : invoice_line.,
					'claim_id' : context['active_id'],
					'selected' : False,
					'state' : 'draft',			
				})
            for line in claim_line_pool.browse(cr,uid,[line_id],context):
                line.set_warranty()
        return {'type': 'ir.actions.act_window_close',}
                        
    # If "Select lines" button pressed
    def action_select_lines(self, cr, uid, ids, context):
        # Add invoice_id to context
        for wiz_obj in self.browse(cr,uid,ids):
            context['invoice_id'] = wiz_obj.invoice_id.id

        return {
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'returned_lines_from_invoice_line.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
                      
returned_lines_from_invoice_invoice()


#===== WIZ STEP 2 : line selection
class returned_lines_from_invoice_lines(osv.osv_memory):
    _name='returned_lines_from_invoice_line.wizard'
    _description='Wizard to create product return lines from invoice'
    _columns = {
        'claim_line_ids' : fields.many2many('temp.claim.line', string='claim lines'),
    }
    
    # Get possible returns from invoice
    def _get_possible_returns_from_invoice(self, cr, uid, context):    
        # Get invoice lines from invoice
        invoice_lines_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', '=', context['invoice_id'])])
        M2M = []
        # Create return lines from invoice lines
        for invoice_line in self.pool.get('account.invoice.line').browse(cr,uid,invoice_lines_ids):
            M2M.append(self.pool.get('temp.claim.line').create(cr, uid, {
					'claim_origine' : "none",
					'invoice_id' : invoice_line.invoice_id.id,
					'invoice_line_id' : invoice_line.id,
					'product_id' : invoice_line.product_id.id,
					'product_returned_quantity' : invoice_line.quantity,
					#'prodlot_id' : invoice_line.,
					'price_unit': invoice_line.price_unit,
				}))
        return M2M

    _defaults = {
        'claim_line_ids': _get_possible_returns_from_invoice,
    }    
    
    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed, for all temp return line create return line
    def action_create_returns(self, cr, uid, ids, context=None):
        for wiz_obj in self.browse(cr,uid,ids):
            for line in wiz_obj.claim_line_ids:
                claim_line_pool = self.pool.get('claim.line')
                line_id = claim_line_pool.create(cr, uid, {
					'claim_origine' : line.claim_origine,
					'invoice_id' : line.invoice_id.id,
					'product_id' : line.product_id.id,
					'product_returned_quantity' : line.product_returned_quantity,
					'unit_sale_price' : line.price_unit,
					#'prodlot_id' : invoice_line.,
					'claim_id' : context['active_id'],
					'selected' : False,		
					'state' : 'draft',	
				}) 
            for line in claim_line_pool.browse(cr,uid,[line_id],context):
                line.set_warranty()
				
        return {
                'type': 'ir.actions.act_window_close',
        }
                           
returned_lines_from_invoice_lines()

#===== Temp returned line
class temp_claim_line(osv.osv_memory):
    """
    Class to handle a product return line (corresponding to one invoice line)
    """
    _name = "temp.claim.line"
    _description = "List of product to return"
    _columns = {
        'claim_origine': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject', required=True, help="To describe the line product problem"),  
        'invoice_id': fields.many2one('account.invoice', 'Invoice'), 
        'invoice_line_id' : fields.many2one('account.invoice.line', 'Invoice line'), 
        'product_id': fields.many2one('product.product', 'Product'),
        'product_returned_quantity' : fields.float('Returned quantity', digits=(12,2), help="Quantity of product returned"),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial / Lot Number'),
        'price_unit': fields.float('Unit sale price', digits=(12,2),),
    }
    
temp_claim_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
