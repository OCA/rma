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
from dateutil.relativedelta import relativedelta
import time
from datetime import datetime

class invoice_line_warranty(osv.osv):
    """
    Class to add a method on the invoice line object to return warranty date and statu
    """
    _name = "account.invoice.line"
    _description = "Add product return functionalities, product exchange and aftersale outsourcing to CRM claim"
    _inherit = 'account.invoice.line'
       
    def get_garantee_limit(self,cr, uid, ids,arg,args,context):   
        claim = self.pool.get('crm.claim').browse(cr,uid,context['active_id'])
        filter = {'value':{'guarantee_limit' : False, 'warning' : False }, 'domain':{}}
        filter['value']['guarantee_limit'] = time.strftime('%Y-%m-%d %H:%M:%S')
        filter['value']['warning'] = 'Valid'
        for invoice_line in self.browse(cr,uid,ids):             
        	if invoice_line.product_id.warranty:
        		filter['value']['guarantee_limit'] = (datetime.strptime(invoice_line.invoice_id.date_invoice, '%Y-%m-%d') + relativedelta(months=int(invoice_line.product_id.warranty))).strftime('%Y-%m-%d')
        	if filter['value']['guarantee_limit'] < claim.date:
        		filter['value']['warning'] = 'Expired'        
        return filter 
    
invoice_line_warranty() 
