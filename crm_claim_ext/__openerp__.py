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


{
    'name': 'CRM claim extension',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Akretion - Emmanuel Samyn
 * Add some fields to CRM claim : canal, spirit, product.exchange
 * Forbid to return product from picking out and in by masking the button

It also contain all views that weren't used when porting this module to v7.0.
Also, all wizard that were not used anymore also landed here in the wait his original
author (Akretion) take a decision on them.

    """,
    'author': 'esamyn',
    'website': 'http://www.erp-236.com',
    'depends': ['crm_claim'],
    'init_xml': [],
    'update_xml': [
        'crm_claim_ext_view.xml',
        'wizard/get_empty_serial_view.xml',
#        'wizard/returned_lines_from_invoice_wizard_view.xml',
#        'wizard/picking_from_returned_lines_wizard_view.xml',
#        'wizard/refund_from_returned_lines_wizard_view.xml',
#        'wizard/exchange_from_returned_lines_wizard_view.xml',
#        'wizard/picking_from_exchange_lines_wizard_view.xml',
    ],
    'demo_xml': [], 
    'test': [], 
    'installable': False,
    'active': False,
    'certificate' : '',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
