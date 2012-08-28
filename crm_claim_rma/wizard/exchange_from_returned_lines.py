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

# Class to create a picking in from selected return lines
class exchange_from_returned_lines(osv.osv_memory):
    _name='exchange_from_returned_lines.wizard'
    _description='Wizard to create an exchange from selected return lines'
    _columns = {
        'exchange_line_ids' : fields.many2many('temp.exchange.line', string='Selected exchange lines'),
    }
    
    # Get selected lines to add to exchange
    def _get_selected_lines(self, cr, uid,context):
        returned_line_ids = self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['return_line_ids'])['return_line_ids'] 
        returned_lines = self.pool.get('return.line').browse(cr, uid,returned_line_ids)
        M2M = []
        for line in returned_lines:
            if True: # ADD ALL LINE line.selected:
                M2M.append(self.pool.get('temp.exchange.line').create(cr, uid, {
					    'name' : "none",
					    'returned_product_id' : line.product_id.id,
					    'returned_product_quantity' : line.product_returned_quantity,
					    'returned_prodlot_id' : line.prodlot_id.id,
					    'returned_unit_sale_price' : line.unit_sale_price,
					    'replacement_product_id': line.product_id.id,
					    'replacement_product_quantity' : line.product_returned_quantity,
				    }))
        return M2M    
   
    _defaults = {
        'exchange_line_ids': _get_selected_lines,
    }    

    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_exchange(self, cr, uid, ids, context=None):
        for exchange in self.browse(cr, uid,ids):
            claim_id = self.pool.get('crm.claim').browse(cr, uid, context['active_id'])
            # create exchange
            for line in exchange.exchange_line_ids:
                exchange_id = self.pool.get('product.exchange').create(cr, uid, {
					    'name' : "#",
					    'state': 'draft',
					    'exchange_send_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					    'returned_product' : line.returned_product_id.id,
					    'returned_product_serial' : line.returned_prodlot_id.id,
					    'returned_product_qty' : line.returned_product_quantity,
					    'returned_unit_sale_price' : line.returned_unit_sale_price,
					    'replacement_product' : line.replacement_product_id.id,
					    'replacement_product_serial' : line.replacement_prodlot_id.id,
					    'replacement_product_qty' : line.replacement_product_quantity,
					    'claim_return_id' : claim_id.id                    
				    })

        return {'type': 'ir.actions.act_window_close',}
                              
exchange_from_returned_lines()

#===== Temp exchange line
class temp_exchange_line(osv.osv_memory):
    """
    Class to handle a product exchange line
    """
    _name = "temp.exchange.line"
    _description = "List of product to exchange"
    _columns = {
        'name': fields.char('Comment', size=128, help="To describe the line product problem"),        
        'returned_product_id': fields.many2one('product.product', 'Returned product', required=True),
        'returned_product_quantity' : fields.float('Returned quantity', digits=(12,2), help="Quantity of product returned"),
        'returned_unit_sale_price' : fields.float('Unit sale price', digits=(12,2),),
        'returned_prodlot_id': fields.many2one('stock.production.lot', 'Returned serial/Lot'),
        'replacement_product_id': fields.many2one('product.product', 'Replacement product', required=True),
        'replacement_product_quantity' : fields.float('Replacement quantity', digits=(12,2), help="Replacement quantity"),
        'replacement_prodlot_id': fields.many2one('stock.production.lot', 'Replacement serial/Lot'),        
    }
    
temp_exchange_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
