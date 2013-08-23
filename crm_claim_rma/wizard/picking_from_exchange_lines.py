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

# Class to create a picking out from selected exchange lines
class picking_out_from_exchange_lines(osv.osv_memory):
    _name='picking_out_from_exchange_lines.wizard'
    _description='Wizard to create a picking out from selected exchange lines'
    _columns = {
        'exchange_line_ids' : fields.many2many('temp.exchange.line', string='Selected exchange lines'),
    }

    # Get selected lines to add to picking in
    def _get_selected_lines(self, cr, uid,context):
        exchange_line_ids = self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['product_exchange_ids'])['product_exchange_ids'] 
        exchange_lines = self.pool.get('product.exchange').browse(cr, uid,exchange_line_ids)
        M2M = []
        for line in exchange_lines:
            if True: #line.selected:
                M2M.append(self.pool.get('temp.exchange.line').create(cr, uid, {
					    'name' : "#",
					    'returned_product_id' : line.returned_product.id,
					    'returned_product_quantity' : line.returned_product_qty,
					    'returned_prodlot_id' : line.returned_product_serial.id,
					    'replacement_product_id': line.replacement_product.id,
                        'replacement_product_quantity' : line.replacement_product_qty,
                        'replacement_prodlot_id': line.replacement_product_serial.id,
				    }))
        return M2M

    _defaults = {
        'exchange_line_ids': _get_selected_lines,
    }

    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        for exchange_lines in self.browse(cr, uid,ids):
            claim_id = self.pool.get('crm.claim').browse(cr, uid, context['active_id'])
            partner_id = claim_id.partner_id.id
            # create picking
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
					    'origin': "RMA/"+`claim_id.id`,
                        'type': 'out',
                        'move_type': 'one', # direct
                        'state': 'draft',
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': claim_id.partner_id.id,
                        'invoice_state': "none",
                        'company_id': claim_id.company_id.id,
                        # 'stock_journal_id': fields.many2one('stock.journal','Stock Journal', select=True),
                        'location_id': self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0],
                        'location_dest_id': claim_id.partner_id.property_stock_customer.id,
					    'note' : 'RMA picking in',
				    })
		    # Create picking lines
            for exchange_line in exchange_lines.exchange_line_ids:
                move_id = self.pool.get('stock.move').create(cr, uid, {
					    'name' : exchange_line.replacement_product_id.name_template, # Motif : crm id ? stock_picking_id ?
					    'priority': '0',
					    #'create_date':
					    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
					    'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
					    'product_id': exchange_line.replacement_product_id.id,
					    'product_qty': exchange_line.replacement_product_quantity,
					    'product_uom': exchange_line.replacement_product_id.uom_id.id,
					    'partner_id': claim_id.partner_id.id,
					    'prodlot_id': exchange_line.replacement_prodlot_id,
					    # 'tracking_id': 
					    'picking_id': picking_id,
					    'state': 'draft',
					    # 'price_unit': 1.0, # to get from invoice line
					    # 'price_currency_id': claim_id.company_id.currency_id.id, # from invoice ???
					    'company_id': claim_id.company_id.id,
					    'location_id': self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0],
					    'location_dest_id': claim_id.partner_id.property_stock_customer.id,
					    'note': 'RMA Refound',
				    })
        view = {
            'name': 'Customer Picking OUT',
            'view_type': 'form',
            'view_mode': 'tree,form', 
            'domain' : "[('type', '=', 'out'),('partner_id','=',%s)]"%partner_id, 
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        return view

picking_out_from_exchange_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
