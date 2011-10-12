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


{
    'name': 'CRM Product Return',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
Add product return functionalities, product exchange and aftersale outsourcing to CRM claim
    """,
    'author': 'Akretion - Emmanuel Samyn',
    'website': 'http://www.akretion.com',
    'depends': ['sale','stock','crm_claim'],
    'init_xml': ['rma_substate_data.xml',],
    'update_xml': [
                'wizard/returned_lines_from_serial_wizard_view.xml',
                'wizard/returned_lines_from_invoice_wizard_view.xml',
                'wizard/picking_from_returned_lines_wizard_view.xml',
                'wizard/refund_from_returned_lines_wizard_view.xml',
                'wizard/exchange_from_returned_lines_wizard_view.xml',
                'wizard/picking_from_exchange_lines_wizard_view.xml',
                'wizard/get_empty_serial_view.xml',
                'crm_claim_rma_view.xml',
                

#        'security/ir.model.access.csv',
 #       'report/crm_claim_report_view.xml',
    ],
    'demo_xml': [
 #       'crm_claim_demo.xml',
    ], 
#    'test': ['test/test_crm_claim.yml'], 
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
