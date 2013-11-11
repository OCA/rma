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
import pooler


class get_empty_serial(orm.TransientModel):
    _name='get_empty_serial.wizard'
    _description='' # Get possible serial for this return based on claim partner, product, invoice
    _columns = {
#        'prodlot_ids': fields.many2many('temp.return.line', 'return_rel', 'wizard_id', 'temp_return_line_id', 'Return lines'),
#        'prodlot_ids': fields.many2one('stock.production.lot', 'Serial / Lot Number 1', required=True),
        'temp': fields.text('Resultats'), 
    }
    
    # 
    def temp_display_results(self, cr, uid, context):
        print "=====> IN TEMP display"
        temp_display = ""
        print "partner_id : ",self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['partner_id'])['partner_id']
#        print "partner_id : ",self.pool.get('crm.claim').read(cr, uid, context['active_id'], ['partner_id'])['partner_id']
        print context
#        for return_line in self.browse(cr,uid,context):
#            print "product_id : ",return_line.product_id.id       
        return temp_display      

    _defaults = {
        'temp': temp_display_results,
    }
    
    # If "Cancel" button pressed
#    def action_cancel(self,cr,uid,ids,conect=None):
#        return {'type': 'ir.actions.act_window_close',}
    
    # If "Add & close" button pressed
#    def action_add_and_close(self, cr, uid, ids, context=None):
#        self.add_return_lines(cr, uid, ids, context)    
#        return {'type': 'ir.actions.act_window_close',}    
                      
get_empty_serial()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
