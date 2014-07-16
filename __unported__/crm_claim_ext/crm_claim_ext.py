# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn						#
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
#from crm import crm
#from datetime import datetime
#from dateutil.relativedelta import relativedelta
#import time

class crm_claim_ext(osv.osv):
    """
    Crm claim field extension
    """
    _name = "crm.claim"
    _description = "Add some fields to crm_claim"
    _inherit = 'crm.claim'
    _columns = {
        'canal_id': fields.many2one('res.partner.canal', 'Channel'),
        'som': fields.many2one('res.partner.som', 'State of Mind'),
        'product_exchange_ids': fields.one2many('product.exchange', 'claim_return_id', 'Product exchanges'),
                # Aftersale outsourcing        
#        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
#        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),


    }
crm_claim_ext()    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
