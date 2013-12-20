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
from openerp.osv import fields, orm


class returned_lines_from_serial(orm.TransientModel):

    _name = 'returned_lines_from_serial.wizard'
    _description = 'Wizard to create product return lines from serial numbers'
    _columns = {
        'prodlot_id_1': fields.many2one('stock.production.lot',
            'Serial / Lot Number 1', required=True),
        'prodlot_id_2': fields.many2one('stock.production.lot',
            'Serial / Lot Number 2'),
        'prodlot_id_3': fields.many2one('stock.production.lot',
            'Serial / Lot Number 3'),
        'prodlot_id_4': fields.many2one('stock.production.lot',
            'Serial / Lot Number 4'),
        'prodlot_id_5': fields.many2one('stock.production.lot',
            'Serial / Lot Number 5'),
        'qty_1' : fields.float('Quantity 1', digits=(12,2), required=True),
        'qty_2' : fields.float('Quantity 2', digits=(12,2)),
        'qty_3' : fields.float('Quantity 3', digits=(12,2)),
        'qty_4' : fields.float('Quantity 4', digits=(12,2)),
        'qty_5' : fields.float('Quantity 5', digits=(12,2)),
        'claim_1': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject',
                                    required=True,
                                    help="To describe the product problem"),  
        'claim_2': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject',
                                    required=True,
                                    help="To describe the line product problem"),
        'claim_3': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject',
                                    required=True,
                                    help="To describe the line product problem"),
        'claim_4': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject',
                                    required=True,
                                    help="To describe the line product problem"),
        'claim_5': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject',
                                    required=True,
                                    help="To describe the line product problem"),
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }
    
    # Get partner from case is set to filter serials
    def _get_default_partner_id(self, cr, uid, context):
        return self.pool.get('crm.claim').read(cr, uid,
            context['active_id'], ['partner_id'])['partner_id'][0]    

    _defaults = {
        'qty_1': lambda *a: 1.0,
        'qty_2': lambda *a: 1.0,
        'qty_3': lambda *a: 1.0,
        'qty_4': lambda *a: 1.0,
        'qty_5': lambda *a: 1.0,
        'claim_1': lambda *a: "none",
        'claim_2': lambda *a: "none",
        'claim_3': lambda *a: "none",
        'claim_4': lambda *a: "none",
        'claim_5': lambda *a: "none",
        'partner_id': _get_default_partner_id,
    }
    
    # If "Cancel" button pressed
    def action_cancel(self,cr,uid,ids,conect=None):
        return {'type': 'ir.actions.act_window_close',}
    
    # If "Add & close" button pressed
    def action_add_and_close(self, cr, uid, ids, context=None):
        self.add_return_lines(cr, uid, ids, context)    
        return {'type': 'ir.actions.act_window_close',}
    
    # If "Add & new" button pressed    
    def action_add_and_new(self, cr, uid, ids, context=None):
        self.add_return_lines(cr, uid, ids, context)
        return {
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'returned_lines_from_serial.wizard',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    
    # Method to get the product id from set
    def get_product_id(self, cr, uid,ids,product_set, context=None):
        product_id = False
        for product in self.prodlot_2_product(cr, uid,[product_set]):
            product_id = product
        return product_id

    # Method to create return lines
    def add_return_lines(self, cr, uid, ids, context=None):
        result = self.browse(cr,uid,ids)[0]
        return_line = self.pool.get('claim.line')
        # Refactor code : create 1 "createmethode" called by each if with values as parameters    
        return_line.create(cr, uid, {
                    'claim_id': context['active_id'],
                    'claim_origine': result.claim_1,
                    'product_id' : self.get_product_id(cr, uid, ids,
                        result.prodlot_id_1.id, context=context),
                    #'invoice_id' : self.prodlot_2_invoice(cr, uid,[result.prodlot_id_1.id],[result.prodlot_id_1.product_id.id]), #PRODLOT_ID can be in many invoice !!
                    'product_returned_quantity' : result.qty_1,
                    'prodlot_id' : result.prodlot_id_1.id,
					'selected' : False,		
					'state' : 'draft',                    
					#'guarantee_limit' : warranty['value']['guarantee_limit'],
					#'warning' : warranty['value']['warning'],
               }) 
        if result.prodlot_id_2.id : 
            return_line.create(cr, uid, {
                    'claim_id': context['active_id'],
                    'claim_origine': result.claim_2,
                    'product_id' : self.get_product_id(cr, uid, ids,
                        result.prodlot_id_2.id, context=context),
#                    'invoice_id' : self.prodlot_2_invoice(cr, uid,[result.prodlot_id_1.id]),
                    'product_returned_quantity' : result.qty_2,
                    'prodlot_id' : result.prodlot_id_2.id,
					'selected' : False,		
					'state' : 'draft',                    
					#'guarantee_limit' : warranty['value']['guarantee_limit'],
					#'warning' : warranty['value']['warning'],
               })
        if result.prodlot_id_3.id : 
            return_line.create(cr, uid, {
                    'claim_id': context['active_id'],
                    'claim_origine': result.claim_3,
                    'product_id' : self.get_product_id(cr, uid, ids,
                        result.prodlot_id_3.id, context=context),
#                    'invoice_id' : self.prodlot_2_invoice(cr, uid,[result.prodlot_id_1.id]),
                    'product_returned_quantity' : result.qty_3,
                    'prodlot_id' : result.prodlot_id_3.id,
                    'selected' : False,		
					'state' : 'draft', 
					#'guarantee_limit' : warranty['value']['guarantee_limit'],
					#'warning' : warranty['value']['warning'],
               })
        if result.prodlot_id_4.id : 
            return_line.create(cr, uid, {
                    'claim_id': context['active_id'],
                    'claim_origine': result.claim_4,
                    'product_id' : self.get_product_id(cr, uid, ids,
                        result.prodlot_id_4.id, context=context),
#                    'invoice_id' : self.prodlot_2_invoice(cr, uid,[result.prodlot_id_1.id]),
                    'product_returned_quantity' : result.qty_4,
                    'prodlot_id' : result.prodlot_id_4.id,
                    'selected' : False,		
					'state' : 'draft', 
					#'guarantee_limit' : warranty['value']['guarantee_limit'],
					#'warning' : warranty['value']['warning'],
               })
        if result.prodlot_id_5.id : 
            return_line.create(cr, uid, {
                    'claim_id': context['active_id'],
                    'claim_origine': result.claim_5,
                    'product_id' : self.get_product_id(cr, uid, ids,
                        result.prodlot_id_5.id, context=context),
#                    'invoice_id' : self.prodlot_2_invoice(cr, uid,[result.prodlot_id_1.id],[result.prodlot_id_1.product_id.id]),
                    'product_returned_quantity' : result.qty_5,
                    'prodlot_id' : result.prodlot_id_5.id,
                    'selected' : False,		
					'state' : 'draft', 
					#'guarantee_type':
					#'guarantee_limit' : warranty['value']['guarantee_limit'],
					#'warning' : warranty['value']['warning'],					
               })  					
					                 
        return True
        
    def prodlot_2_product(self,cr, uid, prodlot_ids):          
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, 
            [('prodlot_id', 'in', prodlot_ids)])
        res = self.pool.get('stock.move').read(cr, uid, 
            stock_move_ids, ['product_id'])
        return set([x['product_id'][0] for x in res if x['product_id']])
        
    def prodlot_2_invoice(self,cr, uid, prodlot_id,product_id):
        # get stock_move_ids
        stock_move_ids = self.pool.get('stock.move').search(cr, uid,
            [('prodlot_id', 'in', prodlot_id)])
        # if 1 id
            # (get stock picking (filter on out ?))
            # get invoice_ids from stock_move_id where invoice.line.product = prodlot_product and invoice customer = claim_partner
            # if 1 id
                # return invoice_id
            # else
        # else : move_in / move_out ; 1 move per order line so if many order lines with same lot, ...
        
        
        #
        #return set(self.stock_move_2_invoice(cr, uid, stock_move_ids))
        return True

    def stock_move_2_invoice(self, cr, uid, stock_move_ids):
        inv_line_ids = []
        res = self.pool.get('stock.move').read(cr, uid,
            stock_move_ids, ['sale_line_id'])
        sale_line_ids = [x['sale_line_id'][0] for x in res if x['sale_line_id']]
        if not sale_line_ids:
            return []
        sql_base = "select invoice_id from sale_order_line_invoice_rel where \
         order_line_id in ("
        cr.execute(sql_base + ','.join(map(lambda x: str(x),sale_line_ids))+')')
        res = cr.fetchall()     
        for i in res:
            for j in i:
                inv_line_ids.append(j)

        res = self.pool.get('account.invoice.line').read(cr, uid,
            inv_line_ids,['invoice_id'])
        return [x['invoice_id'][0] for x in res if x['invoice_id']]  

             