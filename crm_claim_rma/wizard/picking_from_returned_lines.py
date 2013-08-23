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
class picking_in_from_returned_lines(osv.osv_memory):
    _name='picking_in_from_returned_lines.wizard'
    _description='Wizard to create a picking in from selected return lines'
    _columns = {
        'claim_line_location' : fields.many2one('stock.location', 'Dest. Location',help="Location where the system will stock the returned products.", select=True),
        'claim_line_ids' : fields.many2many('temp.claim.line',string='Selected return lines'),
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

    # Get default destination location
    def _get_dest_loc(self, cr, uid,context):
        return self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0]  

    _defaults = {
        'claim_line_ids': _get_selected_lines,
        'claim_line_location' : _get_dest_loc,
    }

    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        print "context", context
        partner_id = 0
#        wf_service = netsvc.LocalService("workflow")
        for picking in self.browse(cr, uid,ids):
            claim_id = self.pool.get('crm.claim').browse(cr, uid, context['active_id'])
            partner_id = claim_id.partner_id.id
            # location type
            location = -1
            if claim_id.claim_type == "customer":
                location = claim_id.partner_id.property_stock_customer.id
            else:
                location = claim_id.partner_id.property_stock_supplier.id
            # create picking
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                        'origin': claim_id.sequence,
                        'type': 'in',
                        'move_type': 'one', # direct
                        'state': 'draft',
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': claim_id.partner_id.id,
                        'invoice_state': "none",
                        'company_id': claim_id.company_id.id,
                        'location_id': location,
                        'location_dest_id': picking.claim_line_location.id,
                        'note' : 'RMA picking in',
                        'claim_id': claim_id.id,
                    })
            # Create picking lines
            for picking_line in picking.claim_line_ids:
                move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name' : picking_line.product_id.name_template, # Motif : crm id ? stock_picking_id ?
                        'priority': '0',
                        #'create_date':
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_id': picking_line.product_id.id,
                        'product_qty': picking_line.product_returned_quantity,
                        'product_uom': picking_line.product_id.uom_id.id,
                        'partner_id': claim_id.partner_id.id,
                        'prodlot_id': picking_line.prodlot_id.id,
                        # 'tracking_id': 
                        'picking_id': picking_id,
                        'state': 'draft',
                        'price_unit': picking_line.price_unit,
                        # 'price_currency_id': claim_id.company_id.currency_id.id, # from invoice ???
                        'company_id': claim_id.company_id.id,
                        'location_id': location,
                        'location_dest_id': picking.claim_line_location.id,
                        #self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0],
                        'note': 'RMA Refound',
                    })

        return {
            'name': 'Customer Picking IN',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain' : "[('type', '=', 'in'),('partner_id','=',%s)]"%partner_id,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }

picking_in_from_returned_lines()

# Class to create a picking out from selected return lines
class picking_out_from_returned_lines(osv.osv_memory):
    _name='picking_out_from_returned_lines.wizard'
    _description='Wizard to create a picking out from selected return lines'
    _columns = {
        'claim_line_ids' : fields.many2many('temp.claim.line', string='Selected return lines'),
    }

    # Get selected lines to add to picking in
    def _get_selected_lines(self, cr, uid,context):
        returned_line_ids = self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['claim_line_ids'])['claim_line_ids'] 
        returned_lines = self.pool.get('claim.line').browse(cr, uid,returned_line_ids)
        M2M = []
        for line in returned_lines:
            if True: # line.selected:
                M2M.append(self.pool.get('temp.claim.line').create(cr, uid, {
                        'claim_origine' : "none",
                        'invoice_id' : line.invoice_line_id.invoice_id.id,
                        'product_id' : line.product_id.id,
                        'product_returned_quantity' : line.product_returned_quantity,
                        'prodlot_id' :  line.prodlot_id.id,
                        'price_unit' :  line.unit_sale_price,
                    }))
        return M2M

    _defaults = {
        'claim_line_ids': _get_selected_lines,
    }

    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,context=None):
        return {'type': 'ir.actions.act_window_close',}

    # If "Create" button pressed
    def action_create_picking(self, cr, uid, ids, context=None):
        partner_id = 0
        for picking in self.browse(cr, uid,ids):
            claim_id = self.pool.get('crm.claim').browse(cr, uid, context['active_id'])
            partner_id = claim_id.partner_id.id
            # location type
            location = -1
            if claim_id.claim_type == "customer":
                location = claim_id.partner_id.property_stock_customer.id
            else:
                location = claim_id.partner_id.property_stock_supplier.id
            # create picking
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                        'origin': claim_id.sequence,
                        'type': 'out',
                        'move_type': 'one', # direct
                        'state': 'draft',
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': claim_id.partner_id.id,
                        'invoice_state': "none",
                        'company_id': claim_id.company_id.id,
                        # 'stock_journal_id': fields.many2one('stock.journal','Stock Journal', select=True),
                        'location_id': self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0],
                        'location_dest_id': location,
                        'note' : 'RMA picking in',
                    })

            # Create picking lines
            for picking_line in picking.claim_line_ids:
                move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name' : picking_line.product_id.name_template, # Motif : crm id ? stock_picking_id ?
                        'priority': '0',
                        #'create_date':
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_id': picking_line.product_id.id,
                        'product_qty': picking_line.product_returned_quantity,
                        'product_uom': picking_line.product_id.uom_id.id,
                        'partner_id': claim_id.partner_id.id,
                        'prodlot_id': picking_line.prodlot_id.id,
                        # 'tracking_id': 
                        'picking_id': picking_id,
                        'state': 'draft',
                        'price_unit': picking_line.price_unit,
                        # 'price_currency_id': claim_id.company_id.currency_id.id, # from invoice ???
                        'company_id': claim_id.company_id.id,
                        'location_id': self.pool.get('stock.warehouse').read(cr, uid, [1],['lot_input_id'])[0]['lot_input_id'][0],
                        'location_dest_id': location,
                        'note': 'RMA Refound',
                    })

        return {
            'name': 'Customer Picking OUT',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain' : "[('type', '=', 'out'),('partner_id','=',%s)]"%partner_id,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }

picking_out_from_returned_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
