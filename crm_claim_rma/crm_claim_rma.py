# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Raphaël Valyi, Sébastien Beau, 	#
# Emmanuel Samyn							#
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
from crm import crm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from tools.translate import _

#=====     TO REFACTORED IN A GENERIC MODULE 
class substate_substate(osv.osv): 
    """
    To precise a state (state=refused; substates= reason 1, 2,...)
    """
    _name = "substate.substate"
    _description = "substate that precise a given state"
    _columns = {
        'name': fields.char('Sub state', size=128, required=True),
        'substate_descr' : fields.text('Description', help="To give more information about the sub state"), 
        # ADD OBJECT TO FILTER
        }
substate_substate()

#=====
class return_line(osv.osv):
    """
    Class to handle a product return line (corresponding to one invoice line)
    """
    _name = "return.line"
    _description = "List of product to return"
        
    # Method to calculate total amount of the line : qty*UP
    def _line_total_amount(self, cr, uid, ids, field_name, arg,context):
        res = {}
        for line in self.browse(cr,uid,ids):            
        	res[line.id] = line.unit_sale_price*line.product_returned_quantity
        return res 
        
    def _get_claim_seq(self, cr, uid, ids, field_name, arg,context):
        res = {}
        for line in self.browse(cr,uid,ids):            
        	res[line.id] = line.claim_id.sequence
        return res          
            	
    _columns = {
        'name': fields.function(_get_claim_seq, method=True, string='Claim n°', type='char', size=64,store=True),
        'claim_origine': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject', required=True, help="To describe the line product problem"),
        'claim_descr' : fields.text('Claim description', help="More precise description of the problem"),  
        'invoice_id': fields.many2one('account.invoice', 'Invoice',help="The invoice related to the returned product"),
        'product_id': fields.many2one('product.product', 'Product',help="Returned product"),
        'product_returned_quantity' : fields.float('Quantity', digits=(12,2), help="Quantity of product returned"),
        'unit_sale_price' : fields.float('Unit sale price', digits=(12,2), help="Unit sale price of the product. Auto filed if retrun done by invoice selection. BE CAREFUL AND CHECK the automatic value as don't take into account previous refounds, invoice discount, can be for 0 if product for free,..."),
        'return_value' : fields.function(_line_total_amount, method=True, string='Total return', type='float', help="Quantity returned * Unit sold price",),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial/Lot n°',help="The serial/lot of the returned product"),
        'applicable_guarantee': fields.selection([('us','Company'),('supplier','Supplier'),('brand','Brand manufacturer')], 'Warranty type'),# METTRE CHAMP FONCTION; type supplier might generate an auto draft forward to the supplier
        'guarantee_limit': fields.date('Warranty limit', help="The warranty limit is computed as: invoice date + warranty defined on selected product.", readonly=True),
        'warning': fields.char('Warranty', size=64, readonly=True,help="If warranty has expired"), #select=1,
        'warranty_type': fields.char('Warranty type', size=64, readonly=True,help="from product form"),
        "warranty_return_partner" : fields.many2one('res.partner.address', 'Warranty return',help="Where the customer has to send back the product(s)"),        
        'claim_id': fields.many2one('crm.claim', 'Related claim',help="To link to the case.claim object"),
        'selected' : fields.boolean('s', help="Check to select"),
        'state' : fields.selection([('draft','Draft'),
                                    ('refused','Refused'),
                                    ('confirmed','Confirmed, waiting for product'),
                                    ('in_to_control','Received, to control'),
                                    ('in_to_treate','Controlled, to treate'),
                                    ('treated','Treated')], 'State'),
        'substate_id': fields.many2one('substate.substate', 'Sub state',help="Select a sub state to precise the standard state. Example 1: state = refused; substate could be warranty over, not in warranty, no problem,... . Example 2: state = to treate; substate could be to refund, to exchange, to repair,..."),
        'last_state_change': fields.date('Last change', help="To set the last state / substate change"),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'name': lambda *a: 'none',
    } 

    # Method to calculate warranty limit
    def set_warranty_limit(self, cr, uid, ids,context,return_line):
        if return_line.invoice_id.date_invoice:
            warning = "Valid"
            if return_line.claim_id.claim_type == 'supplier':
                if return_line.prodlot_id :
                    limit = (datetime.strptime(return_line.invoice_id.date_invoice, '%Y-%m-%d') + relativedelta(months=int(return_line.product_id.seller_ids[0].warranty_duration))).strftime('%Y-%m-%d') # TO BE IMPLEMENTED !!!
                else :
                    limit = (datetime.strptime(return_line.invoice_id.date_invoice, '%Y-%m-%d') + relativedelta(months=int(return_line.product_id.seller_ids[0].warranty_duration))).strftime('%Y-%m-%d') 
            else :
                limit = (datetime.strptime(return_line.invoice_id.date_invoice, '%Y-%m-%d') + relativedelta(months=int(return_line.product_id.warranty))).strftime('%Y-%m-%d')      	            		
            if limit < return_line.claim_id.date:
                warning = 'Expired'
            self.write(cr,uid,ids,{
        	        'guarantee_limit' : limit,
        	        'warning' : warning,
        	        })
        else:
            raise osv.except_osv(_('Error !'), _('Cannot find any date for invoice ! Must be a validated invoice !'))
        return True

    # Method to return the partner delivery address or if none, the default address
    def _get_partner_address(self, cr, uid, ids, context,partner):       
        # dedicated_delivery_address stand for the case a new type of address more particularly dedicated to return delivery would be implemented.
        dedicated_delivery_address_id = self.pool.get('res.partner.address').search(cr, uid, [('partner_id','=',partner.id),('type','like','dedicated_delivery')])
        if dedicated_delivery_address_id:
            return dedicated_delivery_address_id
        else:           
            delivery_address_id = self.pool.get('res.partner.address').search(cr, uid, [('partner_id','=',partner.id),('type','like','delivery')])
            if delivery_address_id: # if delivery address set, use it 
                return delivery_address_id
            else:
                default_address_id = self.pool.get('res.partner.address').search(cr, uid, [('partner_id','=',partner.id),('type','like','default')])
                if default_address_id: # if default address set, use it                   
                    return default_address_id
                else:
                    raise osv.except_osv(_('Error !'), _('Cannot find any address for this product partner !'))
        
    # Method to calculate warranty return address
    def set_warranty_return_address(self, cr, uid, ids,context,return_line):
        return_address = None
        warranty_type = 'company'
        if return_line.prodlot_id :
            # multi supplier method
            print "TO BE IMPLEMENTED"
        else :
            # first supplier method
        	if return_line.product_id.seller_ids[0]:
        	    if return_line.product_id.seller_ids[0].warranty_return_partner:
        	        return_partner = return_line.product_id.seller_ids[0].warranty_return_partner
        	        if return_partner == 'company': 
        	            return_address = self._get_partner_address(cr, uid, ids, context,return_line.claim_id.company_id.partner_id)[0]       	                    
        	        elif return_partner == 'supplier':
        	            return_address = self._get_partner_address(cr, uid, ids, context,return_line.product_id.seller_ids[0].name)[0]
        	            warranty_type = 'supplier'
        	        elif return_partner == 'brand':
        	            return_address = self._get_partner_address(cr, uid, ids, context, return_line.product_id.product_brand_id.partner_id)[0]
        	            warranty_type = 'brand'
        	        else :
        	            warranty_type = 'other'
        	            # TO BE IMPLEMENTED if something to do...
        	    else :
        	        raise osv.except_osv(_('Error !'), _('Cannot find any warranty return partner for this product !'))
        	else : 
        	    raise osv.except_osv(_('Error !'), _('Cannot find any supplier for this product !'))        	    
        self.write(cr,uid,ids,{'warranty_return_partner':return_address,'warranty_type':warranty_type}) 
        return True
               
    # Method to calculate warranty limit and validity
    def set_warranty(self, cr, uid, ids,context=None):
        for return_line in self.browse(cr,uid,ids):             
        	if return_line.product_id and return_line.invoice_id:
        	    self.set_warranty_limit(cr, uid, ids,context,return_line)
        	    self.set_warranty_return_address(cr, uid, ids,context,return_line)
        	else:
        	    raise osv.except_osv(_('Error !'), _('PLEASE SET PRODUCT & INVOICE!'))        	    
        return True 

return_line()

#===== 
class product_exchange(osv.osv): 
    """
    Class to manage product exchanges history
    """
    _name = "product.exchange"
    _description = "exchange history line"
    
    # Method to calculate total amount of the line : qty*UP
    def total_amount_returned(self, cr, uid, ids, field_name, arg,context):
        res = {}
        for line in self.browse(cr,uid,ids):            
        	res[line.id] = line.returned_unit_sale_price*line.returned_product_qty
        return res 

    # Method to calculate total amount of the line : qty*UP
    def total_amount_replacement(self, cr, uid, ids, field_name, arg,context):
        res = {}
        for line in self.browse(cr,uid,ids):            
        	res[line.id] = line.replacement_unit_sale_price*line.replacement_product_qty
        return res 

    # Method to get the replacement product unit price
    def get_replacement_price(self, cr, uid, ids, field_name, arg,context):
        res = {}
        for line in self.browse(cr,uid,ids):            
        	res[line.id] = line.replacement_product.list_price
        return res 
                        
    _columns = {
        'name': fields.char('Comment', size=128, required=True),
        'exchange_send_date' : fields.date('Exchange date'),
        'returned_product' : fields.many2one('product.product', 'Returned product', required=True), # ADD FILTER ON RETURNED PROD
        'returned_product_serial' : fields.many2one('stock.production.lot', 'Returned serial/Lot n°'),
        'returned_product_qty' : fields.float('Returned quantity', digits=(12,2), help="Quantity of product returned"),
        'replacement_product' : fields.many2one('product.product', 'Replacement product', required=True), 
        'replacement_product_serial' : fields.many2one('stock.production.lot', 'Replacement serial/Lot n°'),
        'replacement_product_qty' : fields.float('Replacement quantity', digits=(12,2), help="Quantity of product replaced"),
        'claim_return_id' : fields.many2one('crm.claim', 'Related claim'), # To link to the case.claim object  
        'selected' : fields.boolean('s', help="Check to select"),
        'state' : fields.selection([('draft','Draft'),
                                    ('confirmed','Confirmed'),
                                    ('to_send','To send'),
                                    ('sent','Sent')], 'State'),  
        'returned_unit_sale_price' : fields.float('Unit sale price', digits=(12,2)),
        'returned_value' : fields.function(total_amount_returned, method=True, string='Total return', type='float', help="Quantity exchanged * Unit sold price",),
        'replacement_unit_sale_price' : fields.function(get_replacement_price, method=True, string='Unit sale price', type='float',),
        'replacement_value' : fields.function(total_amount_replacement, method=True, string='Total return', type='float', help="Quantity replaced * Unit sold price",),
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }
    
product_exchange()

#==========        
class crm_claim_product_return(osv.osv):
    """
    Class to add RMA management on a standard crm.claim object
    """
    _name = "crm.claim"
    _description = "Add product return functionalities, product exchange and aftersale outsourcing to CRM claim"
    _inherit = 'crm.claim'
    _columns = {
        'sequence': fields.char('Sequence', size=128,readonly=True,states={'draft': [('readonly', False)]},required=True, help="Company internal claim unique number"),
        'claim_type': fields.selection([('customer','Customer'),
                                    ('supplier','Supplier'),
                                    ('other','Other')], 'Claim type', required=True, help="customer = from customer to company ; supplier = from company to supplier"),
        'return_line_ids' : fields.one2many('return.line', 'claim_id', 'Return lines'),
        'product_exchange_ids': fields.one2many('product.exchange', 'claim_return_id', 'Product exchanges'),
        # Aftersale outsourcing        
#        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
#        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),

        # Financial management
        'planned_revenue': fields.float('Expected revenue'),
        'planned_cost': fields.float('Expected cost'),
        'real_revenue': fields.float('Real revenue'), # A VOIR SI COMPTA ANA ou lien vers compte ana ?
        'real_cost': fields.float('Real cost'), # A VOIR SI COMPTA ANA ou lien vers compte ana ?       
    }
    _defaults = {
        'sequence': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'crm.claim'),
        'claim_type': lambda *a: 'customer',}
       
    #===== Method to select all returned lines =====
    def select_all(self,cr, uid, ids,context):
        return_obj = self.pool.get('return.line')
        for line in self.browse(cr,uid,ids)[0].return_line_ids:
            return_obj.write(cr,uid,line.id,{'selected':True})
        return True
 
    #===== Method to unselect all returned lines =====
    def unselect_all(self,cr, uid, ids,context):
        return_obj = self.pool.get('return.line')
        for line in self.browse(cr,uid,ids)[0].return_line_ids:
            return_obj.write(cr,uid,line.id,{'selected':False})
        return True
    
crm_claim_product_return() 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
