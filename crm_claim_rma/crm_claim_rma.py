# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Raphaël Valyi, Sébastien Beau,     #
# Emmanuel Samyn                            #
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
from crm import crm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT

#TODO: REFACTOR IN A GENERIC MODULE 
class substate_substate(orm.Model): 
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

class claim_line(orm.Model):
    """
    Class to handle a product return line (corresponding to one invoice line)
    """
    _name = "claim.line"
    _description = "List of product to return"
        
    # Method to calculate total amount of the line : qty*UP
    def _line_total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr,uid,ids):            
            res[line.id] = line.unit_sale_price*line.product_returned_quantity
        return res 
        
    _columns = {
        'name': fields.char('Description', size=64,required=True),
        'claim_origine': fields.selection([('none','Not specified'),
                                    ('legal','Legal retractation'),
                                    ('cancellation','Order cancellation'),
                                    ('damaged','Damaged delivered product'),                                    
                                    ('error','Shipping error'),
                                    ('exchange','Exchange request'),
                                    ('lost','Lost during transport'),
                                    ('other','Other')], 'Claim Subject', required=True, help="To describe the line product problem"),
        'claim_descr' : fields.text('Claim description', help="More precise description of the problem"),  
        'product_id': fields.many2one('product.product', 'Product',help="Returned product"),
        'product_returned_quantity' : fields.float('Quantity', digits=(12,2), help="Quantity of product returned"),
        'unit_sale_price' : fields.float('Unit sale price', digits=(12,2), help="Unit sale price of the product. Auto filed if retrun done by invoice selection. BE CAREFUL AND CHECK the automatic value as don't take into account previous refounds, invoice discount, can be for 0 if product for free,..."),
        'return_value' : fields.function(_line_total_amount, method=True, string='Total return', type='float', help="Quantity returned * Unit sold price",),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial/Lot n°',help="The serial/lot of the returned product"),
        'applicable_guarantee': fields.selection([('us','Company'),('supplier','Supplier'),('brand','Brand manufacturer')], 'Warranty type'),# TODO: Replace with function field. type supplier might generate an auto draft forward to the supplier
        'guarantee_limit': fields.date('Warranty limit', help="The warranty limit is computed as: invoice date + warranty defined on selected product.", readonly=True),
        'warning': fields.char('Warranty', size=64, readonly=True,help="If warranty has expired"),
        'warranty_type': fields.char('Warranty type', size=64, readonly=True,help="from product form"),
        "warranty_return_partner" : fields.many2one('res.partner', 'Warranty return',help="Where the customer has to send back the product(s)"),        
        'claim_id': fields.many2one('crm.claim', 'Related claim',help="To link to the case.claim object"),
        'state' : fields.selection([('draft','Draft'),
                                    ('refused','Refused'),
                                    ('confirmed','Confirmed, waiting for product'),
                                    ('in_to_control','Received, to control'),
                                    ('in_to_treate','Controlled, to treate'),
                                    ('treated','Treated')], 'State'),
        'substate_id': fields.many2one('substate.substate', 'Sub state',help="Select a sub state to precise the standard state. Example 1: state = refused; substate could be warranty over, not in warranty, no problem,... . Example 2: state = to treate; substate could be to refund, to exchange, to repair,..."),
        'last_state_change': fields.date('Last change', help="To set the last state / substate change"),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', help='The invoice line related to the returned product'),
        'refund_line_id': fields.many2one('account.invoice.line', 'Refund Line', help='The refund line related to the returned product'),
        'move_in_id': fields.many2one('stock.move', 'Move Line from picking in', help='The move line related to the returned product'),
        'move_out_id': fields.many2one('stock.move', 'Move Line from picking out', help='The move line related to the returned product'),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'name': lambda *a: 'none',
    } 

    # Method to calculate warranty limit
    def set_warranty_limit(self, cr, uid, ids, claim_line, context=None):
        date_invoice = claim_line.invoice_line_id.invoice_id.date_invoice
        if date_invoice:
            warning = "Valid"
            if claim_line.claim_id.claim_type == 'supplier':
                if claim_line.prodlot_id :
                    limit = (datetime.strptime(date_invoice, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=int(claim_line.product_id.seller_ids[0].warranty_duration))).strftime(DEFAULT_SERVER_DATE_FORMAT) # TODO: To be implemented
                else :
                    limit = (datetime.strptime(date_invoice, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=int(claim_line.product_id.seller_ids[0].warranty_duration))).strftime(DEFAULT_SERVER_DATE_FORMAT) 
            else :
                limit = (datetime.strptime(date_invoice, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=int(claim_line.product_id.warranty))).strftime(DEFAULT_SERVER_DATE_FORMAT)
            if limit < claim_line.claim_id.date:
                warning = 'Expired'
            self.write(cr,uid,ids,{
                    'guarantee_limit' : limit,
                    'warning' : warning,
                    })
        else:
            raise osv.except_osv(_('Error !'), _('Cannot find any date for invoice ! Must be a validated invoice !'))
        return True

    # Method to calculate warranty return address
    def set_warranty_return_address(self, cr, uid, ids, claim_line, context=None):
        return_address = None
        warranty_type = 'company'
        seller = claim_line.product_id.seller_info_id
        if seller:
            return_partner = seller.warranty_return_partner
            if return_partner:
                warranty_type = return_partner
            else:
                warranty_type = 'company'
            return_address = seller.warranty_return_address.id
#                if return_partner == 'company': 
#                    return_address = self._get_partner_address(cr, uid, ids, context,claim_line.claim_id.company_id.partner_id)[0]
#                elif return_partner == 'supplier':
#                    return_address = self._get_partner_address(cr, uid, ids, context,claim_line.product_id.seller_ids[0].name)[0]
#                    warranty_type = 'supplier'
#                elif return_partner == 'brand':
#                    return_address = self._get_partner_address(cr, uid, ids, context, claim_line.product_id.product_brand_id.partner_id)[0]
#                    warranty_type = 'brand'
#                else :
#                    warranty_type = 'other'
#                    # TO BE IMPLEMENTED if something to do...
#            else :
#                warranty_type = 'company'
#                return_address = self._get_default_company_address(cr, uid, claim_line.claim_id.company_id, context=context)
                #TODO fix me use default address
#                self.write(cr,uid,ids,{'warranty_return_partner':1,'warranty_type': 'company'})
#                return True

                #raise osv.except_osv(_('Error !'), _('Cannot find any warranty return partner for this product !'))
        else : 
            warranty_type = 'company'
            if claim_line.claim_id.company_id.crm_return_address_id:
                return_address = [claim_line.claim_id.company_id.crm_return_address_id.id]
            else:
                return_address = [claim_line.claim_id.company_id.partner_id.address[0].id]
#            return_address = self._get_default_company_address(cr, uid, claim_line.claim_id.company_id, context=context)
            #TODO fix me use default address
#            self.write(cr,uid,ids,{'warranty_return_partner':1,'warranty_type': 'company'})
#            return True
            #raise osv.except_osv(_('Error !'), _('Cannot find any supplier for this product !'))                
        self.write(cr,uid,ids,{'warranty_return_partner':return_address,'warranty_type':warranty_type}) 
        return True
               
    # Method to calculate warranty limit and validity
    def set_warranty(self, cr, uid, ids, context=None):
        for claim_line in self.browse(cr, uid, ids, context=context):
            if claim_line.product_id and claim_line.invoice_line_id:
                self.set_warranty_limit(cr, uid, ids, claim_line, context)
                self.set_warranty_return_address(cr, uid, ids, claim_line, context)
            else:
                raise osv.except_osv(_('Error !'), _('PLEASE SET PRODUCT & INVOICE!'))
        return True 

#TODO add the option to split the claim_line in order to manage the same product separately

class crm_claim(orm.Model):
    _inherit = 'crm.claim'

    _columns = {
        'number': fields.char('Number', size=128,readonly=True,states={'draft': [('readonly', False)]},required=True, help="Company internal claim unique number"),
        'claim_type': fields.selection([('customer','Customer'),
                                    ('supplier','Supplier'),
                                    ('other','Other')], 'Claim type', required=True, help="customer = from customer to company ; supplier = from company to supplier"),
        'claim_line_ids' : fields.one2many('claim.line', 'claim_id', 'Return lines'),
        'product_exchange_ids': fields.one2many('product.exchange', 'claim_return_id', 'Product exchanges'),
        # Aftersale outsourcing        
#        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
#        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),

        # Financial management
        'planned_revenue': fields.float('Expected revenue'),
        'planned_cost': fields.float('Expected cost'),
        'real_revenue': fields.float('Real revenue'),
        'real_cost': fields.float('Real cost'),
        'invoice_ids': fields.one2many('account.invoice', 'claim_id', 'Refunds'),
        'picking_ids': fields.one2many('stock.picking', 'claim_id', 'RMA'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', help='Related invoice'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
    }
    _defaults = {
        'number': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'crm.claim'),
        'claim_type': lambda *a: 'customer',
        'warehouse_id': lambda *a: 1,
    }

    def onchange_partner_address_id(self, cr, uid, ids, add, email=False, context=None):
        res = super(crm_claim, self).onchange_partner_address_id(cr, uid, ids, add, email=email)
        if add:
            if not res['value']['email_from'] or not res['value']['partner_phone']:
                address = self.pool.get('res.partner').browse(cr, uid, add)
                for other_add in address.partner_id.address:
                    if other_add.email and not res['value']['email_from']:
                        res['value']['email_from'] = other_add.email
                    if other_add.phone and not res['value']['partner_phone']:
                        res['value']['partner_phone'] = other_add.phone
        return res

    def onchange_invoice_id(self, cr, uid, ids, invoice_id, context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_line_ids = invoice_line_obj.search(cr, uid, [('invoice_id', '=', invoice_id)])
        claim_lines = []
        for invoice_line in invoice_line_obj.browse(cr,uid,invoice_line_ids):
#            claim_line_obj = self.pool.get('claim.line')
            claim_lines.append({
                    'name': invoice_line.name,
                    'claim_origine' : "none",
                    'invoice_line_id': invoice_line.id,
                    'product_id' : invoice_line.product_id.id,
                    'product_returned_quantity' : invoice_line.quantity,
                    'unit_sale_price' : invoice_line.price_unit,
#                    'prodlot_id' : invoice_line.,
                    'state' : 'draft',
                })
#            for line in claim_line_obj.browse(cr,uid,[line_id],context):
#                line.set_warranty()
        return  {'value' : {'claim_line_ids' : claim_lines}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
