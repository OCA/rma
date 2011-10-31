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

#=====     
class return_instruction(osv.osv): 
    _name = "return.instruction"
    _description = "Instructions for product return"
    _columns = {
        'name': fields.char('Title', size=128, required=True),
        'instructions' : fields.text('Instructions', help="Instructions for product return"), 
        'is_default' : fields.boolean('Is default', help="If is default, will be use to set the default value in supplier infos. Be careful to have only one default"),
        }
return_instruction()

#=====
class product_supplierinfo(osv.osv):
    _inherit = "product.supplierinfo"

    def get_warranty_return_partner(self, cr, uid, context=None):
        if self.pool.get('ir.module.module').search(cr, uid, [('name','like','product_brand'),('state','like','installed')]):
            return [
                ('company','Company'),
                ('supplier','Supplier'),
                ('brand','Brand manufacturer'),
                ('other','Other'),]
        else:
            return [
                ('company','Company'),
                ('supplier','Supplier'),
                ('other','Other'),]

    # Get selected lines to add to exchange
    def _get_default_instructions(self, cr, uid,context):
        instruction_ids = self.pool.get('return.instruction').search(cr, uid, [('is_default','=','FALSE')])
        if instruction_ids:
            return instruction_ids[0]     
                    
    _columns = {
        "warranty_duration" : fields.float('Warranty', help="Warranty in month for this product/supplier relation. Only for company/supplier relation (purchase order) ; the customer/company relation (sale order) always use the product main warranty field"),
        "warranty_return_partner" :  fields.selection(get_warranty_return_partner, 'Warrantee return', size=128, help="Who is in charge of the warranty return treatment toward the end customer. Company will use the current compagny delivery or default address and so on for supplier and brand manufacturer. Doesn't necessarly mean that the warranty to be applied is the one of the return partner (ie: can be returned to the company and be under the brand warranty"),
        'return_instructions': fields.many2one('return.instruction', 'Instructions',help="Instructions for product return"),
        'active_supplier' : fields.boolean('Active supplier', help=""),
        }
    _defaults = {
        'warranty_return_partner': lambda *a: 'company',
        'return_instructions': _get_default_instructions,
    }
    
product_supplierinfo()   

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
