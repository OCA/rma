# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009-2011  Akretion, Emmanuel Samyn, Benoît Guillot     #
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

from openerp.osv import orm, fields


class return_instruction(orm.Model):
    _name = "return.instruction"
    _description = "Instructions for product return"
    _columns = {
        'name': fields.char('Title', required=True),
        'instructions': fields.text(
            'Instructions',
            help="Instructions for product return"),
        'is_default': fields.boolean(
            'Is default',
            help="If is default, will be use to set the default value in "
                 "supplier infos. Be careful to have only one default"),
    }


class product_supplierinfo(orm.Model):
    _inherit = "product.supplierinfo"

    def get_warranty_return_partner(self, cr, uid, context=None):
        result = [('company', 'Company'),
                  ('supplier', 'Supplier'),
                  ('other', 'Other'),
                  ]
        return result

    def _get_default_instructions(self, cr, uid, context=None):
        """ Get selected lines to add to exchange """
        instr_obj = self.pool.get('return.instruction')
        instruction_ids = instr_obj.search(cr, uid,
                                           [('is_default', '=', 'FALSE')],
                                           context=context)
        if instruction_ids:
            return instruction_ids[0]
        return False

    def _get_warranty_return_address(self, cr, uid, ids, field_names, arg, context=None):
        """ Method to return the partner delivery address or if none, the default address

        dedicated_delivery_address stand for the case a new type of
        address more particularly dedicated to return delivery would be
        implemented.

        """
        result = {}
        for supplier_info in self.browse(cr, uid, ids, context=context):
            result[supplier_info.id] = False
            return_partner = supplier_info.warranty_return_partner
            partner_id = supplier_info.company_id.partner_id.id
            if return_partner:
                if return_partner == 'supplier':
                    partner_id = supplier_info.name.id
                elif return_partner == 'company':
                    if supplier_info.company_id.crm_return_address_id:
                        partner_id = supplier_info.company_id.crm_return_address_id.id
                elif return_partner == 'other':
                    if supplier_info.warranty_return_other_address_id:
                        partner_id = supplier_info.warranty_return_other_address_id.id
                result[supplier_info.id] = partner_id
        return result

    _columns = {
        "warranty_duration": fields.float(
            'Period',
            help="Warranty in month for this product/supplier relation. Only for "
                 "company/supplier relation (purchase order) ; the customer/company "
                 "relation (sale order) always use the product main warranty field"),
        "warranty_return_partner": fields.selection(
            get_warranty_return_partner,
            'Return type',
            required=True,
            help="Who is in charge of the warranty return treatment toward the end customer. "
                 "Company will use the current compagny delivery or default address and so on for "
                 "supplier and brand manufacturer. Doesn't necessarly mean that the warranty to be "
                 "applied is the one of the return partner (ie: can be returned to the company and "
                 "be under the brand warranty"),
        'return_instructions': fields.many2one(
            'return.instruction',
            'Instructions',
            help="Instructions for product return"),
        'active_supplier': fields.boolean(
            'Active supplier',
            help="Is this supplier still active, only for information"),
        'warranty_return_address': fields.function(
            _get_warranty_return_address,
            type='many2one', relation='res.partner', string="Return address",
            help="Where the goods should be returned  "
                 "(computed field based on other infos.)"),
        "warranty_return_other_address_id": fields.many2one(
            'res.partner',
            'Return address',
            help="Where the customer has to send back the product(s) "
                 "if warranty return is set to 'other'."),
    }

    _defaults = {
        'warranty_return_partner': 'company',
        'return_instructions': _get_default_instructions,
    }
